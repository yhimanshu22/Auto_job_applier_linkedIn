"""LinkedIn Automation Framework integration.

Spawns the sibling project `Linkedln-Automation-Framework/main.py` (posting,
engagement, calendar generation, profile pursuit) as isolated subprocesses, with
LinkedIn credentials sourced from the dashboard DB secrets and the cookie file
shared with the parent backend so a single LinkedIn session is reused.

Tasks are tracked in-memory by id; each task gets its own log file under the
runtime logs directory so the dashboard can tail per-task output.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app_paths import get_base_path, get_logs_dir, get_runtime_writable_root
from db_manager import db
from services.linkedin_env import (
    apply_dashboard_automation_settings,
    apply_dashboard_linkedin_credentials,
    apply_linkedin_account,
    get_active_linkedin_account,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def get_framework_dir() -> str:
    """Return the absolute path to the bundled `linkedin_automation` package."""
    return os.path.join(get_base_path(), "linkedin_automation")


def get_shared_cookie_path() -> str:
    """Path to the shared LinkedIn cookie pickle used by both projects."""
    return os.path.join(get_runtime_writable_root(), "linkedin_cookies.pkl")


# ---------------------------------------------------------------------------
# Task tracking (in-memory)
# ---------------------------------------------------------------------------


@dataclass
class AutomationTask:
    id: str
    action: str
    args: list[str]
    log_path: str
    user_id: str = "local-user"
    process: subprocess.Popen | None = field(default=None, repr=False)
    log_handle: Any = field(default=None, repr=False)
    started_at: str = ""
    ended_at: str | None = None
    exit_code: int | None = None
    status: str = "running"
    # LinkedIn account this subprocess authenticates as. Captured at launch
    # from the env that will actually be inherited by the child process.
    account_username: str | None = None

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None


_tasks: dict[str, AutomationTask] = {}
_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Environment construction
# ---------------------------------------------------------------------------


def _build_env(account: str | None = None) -> dict[str, str]:
    """Build the subprocess env: shell env + dashboard creds + framework settings + cookie path + PYTHONPATH.

    When ``account`` is set, the credentials injected by
    ``apply_dashboard_linkedin_credentials`` are overridden so that account's
    username/password are used for this run. When ``account`` is ``None`` or
    empty, the primary account stays in place.
    """
    env = os.environ.copy()
    apply_dashboard_linkedin_credentials(env)
    if account:
        apply_linkedin_account(env, account)
    apply_dashboard_automation_settings(env)
    env["LINKEDIN_COOKIE_PATH"] = get_shared_cookie_path()

    # `python -m linkedin_automation` needs the backend root on sys.path so the
    # package can be imported. The subprocess cwd is the package dir itself
    # (so relative paths like `topics.txt`, `logs/`, `static/` resolve as the
    # framework originally expected), which means PYTHONPATH must do the work
    # of pointing Python at the backend root one level above.
    backend_root = get_base_path()
    existing_pp = env.get("PYTHONPATH", "")
    parts = [backend_root] + ([existing_pp] if existing_pp else [])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


# ---------------------------------------------------------------------------
# Subprocess launch
# ---------------------------------------------------------------------------


def _build_command(action: str, params: dict[str, Any]) -> list[str]:
    """Map an action + params dict to the framework CLI argv."""
    cmd: list[str] = [sys.executable, "-m", "linkedin_automation", action]

    if params.get("debug"):
        cmd.append("--debug")
    if params.get("no_ai"):
        cmd.append("--no-ai")
    # Framework's --headless is a store_true switch; HEADLESS env still applies
    # when the flag is absent. Pass the flag only when True to force headless.
    if params.get("headless"):
        cmd.append("--headless")

    if action == "post":
        if params.get("post_text"):
            cmd += ["--post-text", str(params["post_text"])]
        if params.get("images_dir"):
            cmd += ["--images-dir", str(params["images_dir"])]
        if params.get("no_images"):
            cmd.append("--no-images")
        if params.get("topics_file"):
            cmd += ["--topics-file", str(params["topics_file"])]
        if params.get("schedule_date"):
            cmd += ["--schedule-date", str(params["schedule_date"])]
        if params.get("schedule_time"):
            cmd += ["--schedule-time", str(params["schedule_time"])]

    elif action == "engage":
        if params.get("engage_action"):
            cmd += ["--action", str(params["engage_action"])]
        if params.get("max_actions") is not None:
            cmd += ["--max-actions", str(int(params["max_actions"]))]

    elif action == "pursue":
        profile_name = params.get("profile_name")
        if not profile_name:
            raise ValueError("pursue requires 'profile_name'")
        cmd.append(str(profile_name))
        if params.get("max_posts") is not None:
            cmd += ["--max-posts", str(int(params["max_posts"]))]
        if params.get("perspectives"):
            cmd += ["--perspectives", *map(str, params["perspectives"])]
        if params.get("bio_keywords"):
            cmd += ["--bio-keywords", *map(str, params["bio_keywords"])]
        for flag in ("should_follow", "should_like", "should_comment"):
            if params.get(flag) is False:
                cmd.append(f"--no-{flag.replace('_', '-').replace('should-', '')}")

    elif action == "generate-calendar":
        if not params.get("niche"):
            raise ValueError("generate-calendar requires 'niche'")
        cmd += ["--niche", str(params["niche"])]
        if params.get("total_posts") is not None:
            cmd += ["--total-posts", str(int(params["total_posts"]))]
        if params.get("output"):
            cmd += ["--output", str(params["output"])]

    else:
        raise ValueError(f"Unsupported action: {action}")

    return cmd


def start_task(
    action: str,
    params: dict[str, Any],
    user_id: str = "local-user",
    account: str | None = None,
) -> AutomationTask:
    """Launch a framework subprocess and register it as a tracked task.

    Raises ``FileNotFoundError`` if the framework directory is missing,
    ``ValueError`` for unsupported actions / missing required params, and
    a ``LookupError`` when ``account`` is specified but doesn't match any
    configured account.
    """
    framework_dir = get_framework_dir()
    if not os.path.isdir(framework_dir):
        raise FileNotFoundError(
            f"LinkedIn automation framework not found at {framework_dir}"
        )

    cmd = _build_command(action, params)

    task_id = f"la-{action}-{uuid.uuid4().hex[:8]}"
    logs_dir = get_logs_dir()
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, f"linkedin_automation_{task_id}.log")

    env = _build_env(account=account)
    # Resolve the account that will *actually* authenticate, after dashboard
    # credentials + optional override are applied. This is what we persist on
    # the task / show in the dashboard. ``None`` is possible when no account
    # is configured at all.
    if account:
        resolved = (env.get("LINKEDIN_USERNAME") or "").strip()
        if not resolved or resolved.lower() != str(account).strip().lower():
            raise LookupError(f"LinkedIn account {account!r} not configured")
    account_username = get_active_linkedin_account(env)

    log_handle = open(log_path, "a", encoding="utf-8", buffering=1)
    ts = _now_iso()
    log_handle.write(f"\n{'=' * 60}\n[{ts}] Task {task_id} started\n")
    log_handle.write(f"Action: {action}\nCommand: {' '.join(cmd)}\nCWD: {framework_dir}\n")
    log_handle.write(f"Account: {account_username or '(none configured)'}\n")
    log_handle.write(f"{'=' * 60}\n")
    log_handle.flush()

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

    try:
        process = subprocess.Popen(
            cmd,
            cwd=framework_dir,
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
    except Exception:
        log_handle.close()
        raise

    task = AutomationTask(
        id=task_id,
        action=action,
        args=cmd[2:],
        log_path=log_path,
        user_id=user_id,
        process=process,
        log_handle=log_handle,
        started_at=ts,
        account_username=account_username,
    )

    with _lock:
        _tasks[task_id] = task

    try:
        db.create_automation_task(
            task_id=task_id,
            action=action,
            args=cmd[2:],
            log_path=log_path,
            user_id=user_id,
            account_username=account_username,
        )
    except Exception as exc:
        logging.warning(f"Could not persist automation task {task_id}: {exc}")

    logging.info(
        f"LinkedIn automation task {task_id} started "
        f"(account={account_username}): {' '.join(cmd)}"
    )
    return task


# ---------------------------------------------------------------------------
# Task queries / control
# ---------------------------------------------------------------------------


def _reap(task: AutomationTask) -> None:
    """If the task has finished, capture exit code and close its log handle."""
    if task.process is None:
        return
    rc = task.process.poll()
    if rc is None:
        return
    if task.exit_code is None:
        task.exit_code = rc
        task.ended_at = _now_iso()
        # `stopped` is set by stop_task() prior to reaping; otherwise rely on rc.
        if task.status == "running":
            task.status = "completed" if rc == 0 else "failed"
        if task.log_handle and not task.log_handle.closed:
            try:
                task.log_handle.write(
                    f"\n[{task.ended_at}] Task {task.id} ended (exit_code={rc})\n"
                )
                task.log_handle.flush()
                task.log_handle.close()
            except Exception:
                pass
        try:
            db.finalize_automation_task(task.id, rc, status=task.status)
        except Exception as exc:
            logging.warning(f"Could not finalize automation task {task.id} in DB: {exc}")


def get_task(task_id: str) -> AutomationTask | None:
    with _lock:
        task = _tasks.get(task_id)
    if task:
        _reap(task)
    return task


def list_tasks(limit: int = 50) -> list[AutomationTask]:
    with _lock:
        tasks = list(_tasks.values())
    for t in tasks:
        _reap(t)
    tasks.sort(key=lambda t: t.started_at, reverse=True)
    return tasks[:limit]


def stop_task(task_id: str) -> bool:
    task = get_task(task_id)
    if not task or not task.is_running():
        return False
    task.status = "stopped"
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/PID", str(task.process.pid), "/T"],
                capture_output=True,
            )
        else:
            task.process.terminate()
            try:
                task.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                task.process.kill()
    except Exception as exc:
        logging.warning(f"Failed to stop task {task_id}: {exc}")
        return False
    _reap(task)
    return True


def tail_log(task: AutomationTask, lines: int = 200) -> str:
    if not os.path.isfile(task.log_path):
        return ""
    try:
        with open(task.log_path, "r", encoding="utf-8", errors="replace") as f:
            buf = f.readlines()
        return "".join(buf[-max(20, min(lines, 1000)) :])
    except Exception as exc:
        return f"(log read error: {exc})"


def task_to_dict(task: AutomationTask, include_log: bool = False, log_lines: int = 200) -> dict[str, Any]:
    _reap(task)
    data: dict[str, Any] = {
        "id": task.id,
        "action": task.action,
        "args": task.args,
        "log_path": task.log_path,
        "user_id": task.user_id,
        "started_at": task.started_at,
        "ended_at": task.ended_at,
        "exit_code": task.exit_code,
        "status": task.status,
        "running": task.is_running(),
        "account_username": task.account_username,
    }
    if include_log:
        data["log"] = tail_log(task, log_lines)
    return data


def merged_task_history(limit: int = 50, user_id: Optional[str] = None) -> list[dict[str, Any]]:
    """Combine in-memory live tasks with persisted DB history.

    Live tasks take precedence for the same id (their `running` flag and
    most recent state are authoritative until the process exits).
    """
    live_dicts: dict[str, dict[str, Any]] = {
        t.id: task_to_dict(t, include_log=False) for t in list_tasks(limit=limit)
    }
    try:
        db_rows = db.list_automation_tasks(limit=limit, user_id=user_id)
    except Exception as exc:
        logging.warning(f"Could not load automation task history from DB: {exc}")
        db_rows = []

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for live in live_dicts.values():
        merged.append(live)
        seen.add(live["id"])
    for row in db_rows:
        if row["id"] in seen:
            continue
        row["running"] = False
        merged.append(row)
        seen.add(row["id"])

    merged.sort(key=lambda t: t.get("started_at") or "", reverse=True)
    return merged[:limit]


# ---------------------------------------------------------------------------
# Optional cookie bridge
# ---------------------------------------------------------------------------


def ensure_shared_cookie_path_exists() -> Optional[str]:
    """Touch the shared cookie path so both processes can locate / write to it."""
    path = get_shared_cookie_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path
