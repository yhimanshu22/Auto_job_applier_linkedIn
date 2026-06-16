"""FastAPI routes for the LinkedIn Automation Framework integration.

Exposes posting, engagement, content-calendar generation, and profile pursuit
flows from the sibling `Linkedln-Automation-Framework/` project as HTTP endpoints
the web dashboard can call. Each call spawns an isolated subprocess and
returns a task id the dashboard can poll for logs / status / stop.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Optional

from fastapi import APIRouter, Body, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from db_manager import db
from services.admin import is_admin
from utils.user_resolution import resolve_user_id
from services import linkedin_automation as la
from services.linkedin_env import (
    AUTOMATION_KEY_TO_ENV,
    AUTOMATION_SENSITIVE_KEYS,
    get_automation_settings,
    preview_env_with_dashboard_credentials,
)
from services.plan_limits import (
    AUTOMATION_DAILY_LIMITS,
    assert_can_run_automation,
)


router = APIRouter(prefix="/api/linkedin-automation", tags=["linkedin-automation"])


# ---------------------------------------------------------------------------
# Shared helpers (used by both /stats, /health, and /dashboard)
# ---------------------------------------------------------------------------


def _stats_with_plan(user_id: Optional[str]) -> dict[str, Any]:
    """Stats + plan / daily-limit info for the dashboard summary panel."""
    data = db.get_automation_task_stats(user_id=user_id)
    plan = "free_trial"
    if user_id:
        subscription = db.get_user_subscription(user_id)
        if subscription:
            plan = subscription.get("plan", "free_trial") or "free_trial"
    if is_admin(user_id):
        plan = "agency"
    data["plan"] = plan
    data["daily_limit"] = AUTOMATION_DAILY_LIMITS.get(
        plan, AUTOMATION_DAILY_LIMITS["free_trial"]
    )
    data["daily_used"] = data["last_24h"]
    return data


def _health_snapshot(user_id: str) -> dict[str, Any]:
    """Cheap filesystem probes that report whether the framework is reachable."""
    from services.chrome_profiles import resolve_automation_chrome_profile
    from services.linkedin_session import cookie_store_ids, load_linkedin_cookies

    framework_dir = la.get_framework_dir()
    entrypoint = os.path.join(framework_dir, "__main__.py")
    chrome_profile = resolve_automation_chrome_profile(
        user_id=user_id, linkedin_email=user_id
    )
    has_db_session = bool(
        load_linkedin_cookies(user_id=user_id, linkedin_username=user_id)
    )
    framework_ready = la.is_framework_available()
    return {
        "framework_dir": framework_dir,
        "framework_available": framework_ready,
        "main_py_exists": os.path.isfile(entrypoint),
        "entrypoint_path": entrypoint,
        "session_store": "user_sessions",
        "session_store_ids": cookie_store_ids(user_id=user_id, linkedin_username=user_id),
        "chrome_profile_ready": chrome_profile is not None,
        "chrome_profile_dir": chrome_profile["profile_dir"] if chrome_profile else None,
        "session_in_db": has_db_session or chrome_profile is not None,
    }


def _compute_etag(
    tasks: list[dict[str, Any]],
    stats: dict[str, Any],
    health: dict[str, Any],
    form_defaults: dict[str, Any],
) -> str:
    """Strong ETag derived from the parts of the payload that can actually change.

    Excludes ``log_path`` and absolute filesystem paths in ``health`` so the
    hash is stable across restarts that pick a different temp dir, and so
    benign cosmetic changes don't bust the cache.
    """
    fingerprint = {
        "tasks": [
            (
                t.get("id"),
                t.get("status"),
                t.get("running"),
                t.get("started_at"),
                t.get("ended_at"),
                t.get("exit_code"),
                t.get("account_username"),
            )
            for t in tasks
        ],
        "stats": stats,
        "health": {
            "framework_available": health.get("framework_available"),
            "main_py_exists": health.get("main_py_exists"),
            "session_in_db": health.get("session_in_db"),
            "chrome_profile_ready": health.get("chrome_profile_ready"),
        },
        "form_defaults": form_defaults,
    }
    canonical = json.dumps(fingerprint, sort_keys=True, separators=(",", ":"))
    return '"' + hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:16] + '"'


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class _CommonOpts(BaseModel):
    debug: bool = False
    headless: Optional[bool] = None
    no_ai: bool = False
    user_id: Optional[str] = None


class PostRequest(_CommonOpts):
    post_text: Optional[str] = Field(
        default=None, description="Text to post. Omit to draw a topic from the topics file."
    )
    topics_file: Optional[str] = None
    images_dir: Optional[str] = None
    no_images: bool = False
    schedule_date: Optional[str] = Field(default=None, description="mm/dd/yyyy")
    schedule_time: Optional[str] = Field(default=None, description="e.g. '10:45 AM'")


class EngageRequest(_CommonOpts):
    engage_action: str = Field(default="both", description="like | comment | both")
    max_actions: int = 10


class PursueRequest(_CommonOpts):
    profile_name: str
    max_posts: int = 5
    perspectives: Optional[list[str]] = None
    bio_keywords: Optional[list[str]] = None
    should_follow: bool = True
    should_like: bool = True
    should_comment: bool = True


class ConnectRequest(_CommonOpts):
    query: str = Field(description="People search keywords, e.g. IIT Kanpur")
    max_connects: int = Field(default=10, ge=1, le=50)
    note: Optional[str] = Field(
        default=None, description="Optional connection invitation note (max 300 chars)"
    )
    bio_keywords: Optional[list[str]] = None


class CalendarRequest(_CommonOpts):
    niche: str
    total_posts: int = 30
    output: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _start(action: str, params: dict[str, Any], request: Request) -> dict[str, Any]:
    claimed = params.pop("user_id", None)
    user_id = await resolve_user_id(request, claimed)
    assert_can_run_automation(user_id)
    try:
        task = la.start_task(action, params, user_id=user_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start task: {exc}")
    return la.task_to_dict(task, include_log=False)


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


@router.post("/post")
async def create_post(req: PostRequest, request: Request):
    """Create a LinkedIn post (immediate or scheduled, optional images / AI)."""
    return await _start("post", req.model_dump(exclude_none=True), request)


@router.post("/engage")
async def engage_feed(req: EngageRequest, request: Request):
    """Run the engagement stream (likes / comments)."""
    return await _start("engage", req.model_dump(exclude_none=True), request)


@router.post("/pursue")
async def pursue_profile(req: PursueRequest, request: Request):
    """Pursue a specific profile (follow / like / comment)."""
    return await _start("pursue", req.model_dump(exclude_none=True), request)


@router.post("/connect")
async def connect_people(req: ConnectRequest, request: Request):
    """Search people by keyword and send connection requests."""
    return await _start("connect", req.model_dump(exclude_none=True), request)


@router.post("/calendar")
async def generate_calendar(req: CalendarRequest, request: Request):
    """Generate a content calendar appended to a topics file."""
    return await _start("generate-calendar", req.model_dump(exclude_none=True), request)


# ---------------------------------------------------------------------------
# Task management
# ---------------------------------------------------------------------------


@router.get("/tasks")
async def list_tasks(request: Request, limit: int = 50, user_id: Optional[str] = None):
    """List automation tasks: live in-memory tasks + persisted DB history."""
    uid = await resolve_user_id(request, user_id)
    return {"tasks": la.merged_task_history(limit=limit, user_id=uid)}


def _assert_task_owner(request_user: str, task_user: str | None):
    """Cross-user task access is a 404 (don't leak that the id exists)."""
    from utils.user_resolution import _require_auth

    if _require_auth() and task_user and task_user != request_user:
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/tasks/{task_id}")
async def get_task(
    request: Request,
    task_id: str,
    log_lines: int = 200,
    user_id: Optional[str] = None,
):
    uid = await resolve_user_id(request, user_id)
    task = la.get_task(task_id)
    if task is not None:
        _assert_task_owner(uid, task.user_id)
        return la.task_to_dict(task, include_log=True, log_lines=log_lines)
    # Fall back to persisted history when the process is no longer in memory.
    row = db.get_automation_task(task_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    _assert_task_owner(uid, row.get("user_id"))
    row["running"] = False
    log_path = row.get("log_path")
    if log_path:
        try:
            import os as _os

            if _os.path.isfile(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    buf = f.readlines()
                row["log"] = "".join(buf[-max(20, min(int(log_lines), 1000)) :])
            else:
                row["log"] = f"(log file not found: {log_path})"
        except Exception as exc:
            row["log"] = f"(log read error: {exc})"
    else:
        row["log"] = "(no log path recorded for this task)"
    return row


def _read_framework_file(rel_or_abs_path: str, max_bytes: int) -> dict[str, Any]:
    """Resolve a path against the framework dir, read it safely, return a dict.

    Centralizes the path-traversal guard, size cap, and metadata shape used
    by both ``/tasks/{id}/artifact`` and ``/calendar``. Raises ``HTTPException``
    on guard / read failures so the callers can stay terse.
    """
    framework_dir = os.path.abspath(la.get_framework_dir())
    raw = (
        rel_or_abs_path
        if os.path.isabs(rel_or_abs_path)
        else os.path.join(framework_dir, rel_or_abs_path)
    )
    resolved = os.path.abspath(raw)

    # Only serve files that resolve inside the framework dir even when the
    # caller passed an absolute or ``..``-laced path.
    if (
        not resolved.startswith(framework_dir + os.sep)
        and resolved != framework_dir
    ):
        raise HTTPException(
            status_code=403,
            detail="Artifact path is outside the framework directory.",
        )

    if not os.path.isfile(resolved):
        raise HTTPException(
            status_code=404,
            detail=f"File not found at {os.path.relpath(resolved, framework_dir)!r}",
        )

    try:
        size = os.path.getsize(resolved)
        mtime = os.path.getmtime(resolved)
        cap = max(1024, min(int(max_bytes), 2_000_000))
        truncated = size > cap
        with open(resolved, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read(cap)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read artifact: {exc}")

    return {
        "filename": os.path.basename(resolved),
        "path": os.path.relpath(resolved, framework_dir),
        "absolute_path": resolved,
        "size_bytes": size,
        "mtime": mtime,
        "truncated": truncated,
        "content": content,
    }


@router.get("/tasks/{task_id}/artifact")
async def get_task_artifact(request: Request, task_id: str, max_bytes: int = 200_000):
    """Return the file produced by a task (currently ``generate-calendar``).

    Generation tasks write a topics file to the framework cwd. The dashboard
    calls this endpoint to surface that file inline so users don't have to
    open the filesystem. Restricted to ``generate-calendar`` tasks and to
    paths that resolve inside the framework directory.
    """
    uid = await resolve_user_id(request)
    task = la.get_task(task_id)
    if task is not None:
        _assert_task_owner(uid, task.user_id)
        action = task.action
        args: list[str] = list(task.args)
    else:
        row = db.get_automation_task(task_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        _assert_task_owner(uid, row.get("user_id"))
        action = row.get("action") or ""
        args = list(row.get("args") or [])

    if action != "generate-calendar":
        raise HTTPException(
            status_code=400,
            detail=f"Task action {action!r} has no readable artifact.",
        )

    # Locate the output file: honor a ``--output`` flag if the user passed
    # one, otherwise fall back to the framework default ``content_calendar.txt``.
    output = "content_calendar.txt"
    for i, token in enumerate(args):
        if token == "--output" and i + 1 < len(args):
            output = args[i + 1]
            break
        if token.startswith("--output="):
            output = token.split("=", 1)[1]
            break

    payload = _read_framework_file(output, max_bytes)
    payload["task_id"] = task_id
    payload["action"] = action
    return payload


@router.get("/calendar")
async def get_calendar_file(
    request: Request,
    file: str = "content_calendar.txt",
    max_bytes: int = 200_000,
):
    """Read a content-calendar file directly, independent of any task.

    The Calendar tab uses this to render the current ``content_calendar.txt``
    (or a custom output file) without forcing the user to dig into a task
    modal. Same path-traversal guard as ``/tasks/{id}/artifact``.
    """
    await resolve_user_id(request)
    safe = (file or "").strip() or "content_calendar.txt"
    payload = _read_framework_file(safe, max_bytes)
    payload["action"] = "generate-calendar"
    return payload


@router.post("/tasks/{task_id}/stop")
async def stop_task(request: Request, task_id: str, user_id: Optional[str] = None):
    uid = await resolve_user_id(request, user_id)
    task = la.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    _assert_task_owner(uid, task.user_id)
    stopped = la.stop_task(task_id)
    return {
        "stopped": stopped,
        "task": la.task_to_dict(task, include_log=False),
    }


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


@router.get("/health")
async def health(request: Request, user_id: Optional[str] = None):
    """Report whether the framework is reachable and a DB session exists."""
    uid = await resolve_user_id(request, user_id)
    return _health_snapshot(user_id=uid)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@router.get("/stats")
async def stats(request: Request, user_id: Optional[str] = None):
    """Aggregate counts of automation tasks for the dashboard summary panel."""
    uid = await resolve_user_id(request, user_id)
    return _stats_with_plan(uid)


# ---------------------------------------------------------------------------
# Combined dashboard endpoint (single roundtrip + ETag for cheap 304s)
# ---------------------------------------------------------------------------


@router.get("/dashboard")
async def dashboard(
    request: Request,
    response: Response,
    user_id: Optional[str] = None,
    limit: int = 25,
    if_none_match: Optional[str] = Header(default=None, convert_underscores=True),
):
    """Combined dashboard payload: ``tasks + stats + health`` in one request.

    The frontend polls this every few seconds; ``ETag`` / ``If-None-Match``
    turn unchanged ticks into ``304 Not Modified`` responses (~empty body).

    Keeping ``/tasks``, ``/stats``, and ``/health`` as separate endpoints
    too — they're still useful for one-off refreshes and integration callers.
    """
    uid = await resolve_user_id(request, user_id)
    tasks = la.merged_task_history(limit=limit, user_id=uid)
    stats_payload = _stats_with_plan(uid)
    health_payload = _health_snapshot(user_id=uid)
    form_defaults_payload = _form_defaults_snapshot(user_id=uid)

    etag = _compute_etag(
        tasks,
        stats_payload,
        health_payload,
        form_defaults_payload,
    )
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache"

    # Browsers may send multiple comma-separated tags; we accept any match.
    if if_none_match:
        candidates = {tag.strip() for tag in if_none_match.split(",") if tag.strip()}
        if etag in candidates or "*" in candidates:
            return Response(
                status_code=304,
                headers={"ETag": etag, "Cache-Control": "no-cache"},
            )

    return {
        "tasks": tasks,
        "stats": stats_payload,
        "health": health_payload,
        "form_defaults": form_defaults_payload,
        "etag": etag,
    }


# ---------------------------------------------------------------------------
# Accounts (used by billing dashboard for seat count; not automation identity)
# ---------------------------------------------------------------------------


def _accounts_snapshot(user_id: str) -> dict[str, Any]:
    """Available LinkedIn accounts from secrets (job bot / billing only)."""
    from services.linkedin_env import get_active_linkedin_account, list_linkedin_accounts

    accounts = list_linkedin_accounts(user_id=user_id)
    active = get_active_linkedin_account(user_id=user_id)
    return {
        "accounts": accounts,
        "active": active,
    }


@router.get("/accounts")
async def accounts(request: Request, user_id: Optional[str] = None):
    """List LinkedIn accounts available to run automations as (passwords not echoed)."""
    uid = await resolve_user_id(request, user_id)
    return _accounts_snapshot(user_id=uid)


# ---------------------------------------------------------------------------
# Form defaults — every dashboard input value is mirrored into the DB so the
# UI re-hydrates with the same state on the next session (different machine,
# different browser, after restart, etc.). Stored as a flat dict in DB
# category ``linkedin_automation_form_defaults``.
# ---------------------------------------------------------------------------

FORM_DEFAULTS_CATEGORY = "linkedin_automation_form_defaults"

# Allow-list of keys the frontend may write. Keeping this tight prevents an
# accidental ``localStorage`` dump from polluting the DB and lets us evolve
# the UI without worrying about stale keys lingering. The set covers every
# input rendered on the automation dashboard (tab + account + common flags
# + per-tab form state).
ALLOWED_FORM_KEYS: frozenset[str] = frozenset({
    # page-level
    "tab",
    # common
    "common_debug",
    "common_headless",
    "common_no_ai",
    # post
    "post_text",
    "post_images_dir",
    "post_no_images",
    "post_topics_file",
    "post_schedule_date",
    "post_schedule_time",
    # engage
    "engage_action",
    "engage_max_actions",
    # pursue
    "pursue_profile_name",
    "pursue_max_posts",
    "pursue_perspectives",
    "pursue_bio_keywords",
    "pursue_do_follow",
    "pursue_do_like",
    "pursue_do_comment",
    # connect
    "connect_query",
    "connect_max_connects",
    "connect_note",
    "connect_bio_keywords",
    # calendar
    "calendar_niche",
    "calendar_total_posts",
    "calendar_output",
})


def _form_defaults_snapshot(user_id: str) -> dict[str, Any]:
    """Read the current form-defaults blob from the DB, returning {} on failure.

    Strips two classes of stale entries from the result:
      * unknown keys (not in :data:`ALLOWED_FORM_KEYS`) — legacy data or
        anything inserted before we tightened the allow-list.
      * keys whose value is ``None`` — left behind by older clear-paths
        that wrote nulls instead of deleting the row.
    """
    try:
        cfg = db.get_all_by_category(FORM_DEFAULTS_CATEGORY, user_id=user_id) or {}
        if not isinstance(cfg, dict):
            return {}
        return {
            k: v
            for k, v in cfg.items()
            if k in ALLOWED_FORM_KEYS and v is not None
        }
    except Exception:
        return {}


@router.get("/form-defaults")
async def get_form_defaults(request: Request, user_id: Optional[str] = None):
    """Return the persisted dashboard form values (empty dict when nothing saved)."""
    uid = await resolve_user_id(request, user_id)
    return _form_defaults_snapshot(user_id=uid)


@router.put("/form-defaults")
async def put_form_defaults(
    request: Request,
    payload: dict[str, Any] = Body(default_factory=dict),
    user_id: Optional[str] = None,
):
    """Merge ``payload`` into the stored form-defaults blob.

    Keys absent from ``payload`` are left untouched. Keys with value ``None``
    are **deleted** from the store so the frontend can clear individual
    fields. Unknown keys are silently dropped so the DB stays clean.
    """
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400, detail="Body must be a JSON object"
        )

    unknown = [k for k in payload if k not in ALLOWED_FORM_KEYS]
    if unknown:
        # 400 instead of silent drop so the frontend hears about typos.
        raise HTTPException(
            status_code=400,
            detail=f"Unknown form-defaults keys: {sorted(unknown)}",
        )

    uid = await resolve_user_id(request, user_id)
    for k, v in payload.items():
        if v is None:
            # Treat ``None`` as "forget this key" so the listing endpoint
            # doesn't return a phantom entry with a null value.
            db.delete_config(k, FORM_DEFAULTS_CATEGORY, user_id=uid)
        else:
            db.set_config(k, v, FORM_DEFAULTS_CATEGORY, user_id=uid)

    return {"status": "saved", "defaults": _form_defaults_snapshot(user_id=uid)}


@router.delete("/form-defaults")
async def clear_form_defaults(request: Request, prefix: Optional[str] = None, user_id: Optional[str] = None):
    """Drop all stored defaults, or only those whose key starts with ``prefix``.

    The dashboard's "Clear saved defaults" buttons pass a per-form prefix
    (e.g. ``post_``, ``engage_``) so a single tab can be reset without
    wiping the others.
    """
    uid = await resolve_user_id(request, user_id)
    cfg = _form_defaults_snapshot(user_id=uid)
    keys_to_clear = (
        [k for k in cfg if k.startswith(prefix)] if prefix else list(cfg.keys())
    )
    for k in keys_to_clear:
        db.delete_config(k, FORM_DEFAULTS_CATEGORY, user_id=uid)
    return {"status": "cleared", "removed": keys_to_clear}


# ---------------------------------------------------------------------------
# Settings (DB category: linkedin_automation)
# ---------------------------------------------------------------------------


class AutomationSettings(BaseModel):
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    use_gemini: Optional[bool] = None
    linkedin_ai_provider: Optional[str] = None
    grok_api_key: Optional[str] = None
    grok_model: Optional[str] = None
    groq_api_key: Optional[str] = None
    groq_model: Optional[str] = None
    headless: Optional[bool] = None
    marketing_mode: Optional[bool] = None
    project_name: Optional[str] = None
    project_url: Optional[str] = None
    project_pitch: Optional[str] = None
    project_short_pitch: Optional[str] = None
    project_context: Optional[str] = None
    project_tagline: Optional[str] = None
    linkedin_resume_url: Optional[str] = None
    linkedin_github_username: Optional[str] = None
    linkedin_comment_display_name: Optional[str] = None
    linkedin_comment_voice: Optional[str] = None


_SENTINEL_PRESERVE = {"set", "***", "********"}


@router.get("/config")
async def read_settings(request: Request, user_id: Optional[str] = None):
    """Return the dashboard-managed framework settings (API keys masked)."""
    uid = await resolve_user_id(request, user_id)
    return get_automation_settings(mask_sensitive=True, user_id=uid)


@router.post("/config")
async def write_settings(payload: AutomationSettings, request: Request, user_id: Optional[str] = None):
    """Upsert framework settings into the DB (sensitive values are encrypted)."""
    uid = await resolve_user_id(request, user_id)
    incoming = payload.model_dump(exclude_unset=True)
    if not incoming:
        raise HTTPException(status_code=400, detail="No settings provided.")

    for key, value in incoming.items():
        if key not in AUTOMATION_KEY_TO_ENV:
            continue
        # Allow the UI to leave masked sensitive values alone by sending the
        # sentinel string back; only overwrite when an actual value is provided.
        if (
            key in AUTOMATION_SENSITIVE_KEYS
            and isinstance(value, str)
            and value.strip() in _SENTINEL_PRESERVE
        ):
            continue
        if isinstance(value, str):
            value = value.strip()
        db.set_config(key, value, category="linkedin_automation", user_id=uid)

    return {
        "status": "ok",
        "settings": get_automation_settings(mask_sensitive=True, user_id=uid),
    }
