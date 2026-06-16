"""Saved Connect search presets with optional daily schedule and run history."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from db_manager import db
from services import linkedin_automation as la
from services.plan_limits import assert_can_run_automation

CONNECT_CAMPAIGNS_CATEGORY = "linkedin_connect_campaigns"
CAMPAIGNS_KEY = "connect_campaigns"
TASK_MAP_CATEGORY = "linkedin_connect_campaign_task_map"
MAX_RUN_HISTORY = 50

_CONNECT_SUMMARY_RE = re.compile(
    r"Connect summary:\s*sent=(\d+)\s+skipped=(\d+)", re.IGNORECASE
)
_CONNECT_JSON_RE = re.compile(
    r'"sent"\s*:\s*(\d+).*?"skipped"\s*:\s*(\d+)', re.DOTALL
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_connect_log(log_path: str | None) -> tuple[int, int]:
    """Best-effort sent/skipped counts from a connect task log file."""
    if not log_path:
        return 0, 0
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return 0, 0

    m = _CONNECT_SUMMARY_RE.search(text)
    if m:
        return int(m.group(1)), int(m.group(2))

    m = _CONNECT_JSON_RE.search(text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0


def _load_campaigns_raw(user_id: str) -> list[dict[str, Any]]:
    cfg = db.get_all_by_category(CONNECT_CAMPAIGNS_CATEGORY, user_id=user_id) or {}
    blob = cfg.get(CAMPAIGNS_KEY)
    if isinstance(blob, list):
        return [c for c in blob if isinstance(c, dict) and c.get("id")]
    return []


def _save_campaigns_raw(user_id: str, campaigns: list[dict[str, Any]]) -> None:
    db.set_config(CAMPAIGNS_KEY, campaigns, CONNECT_CAMPAIGNS_CATEGORY, user_id=user_id)


def _normalize_campaign(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    now = _now_iso()
    base = dict(existing or {})
    name = str(payload.get("name") or base.get("name") or "").strip()
    query = str(payload.get("query") or base.get("query") or "").strip()
    if not name:
        raise ValueError("Campaign name is required")
    if not query:
        raise ValueError("Search query is required")

    max_connects = int(payload.get("max_connects", base.get("max_connects", 10)))
    max_connects = max(1, min(50, max_connects))

    daily_max = payload.get("daily_max", base.get("daily_max"))
    if daily_max is not None:
        daily_max = max(1, min(50, int(daily_max)))

    bio_raw = payload.get("bio_keywords", base.get("bio_keywords"))
    bio_keywords: list[str] | None
    if bio_raw is None:
        bio_keywords = None
    elif isinstance(bio_raw, str):
        bio_keywords = [x.strip() for x in bio_raw.split(",") if x.strip()] or None
    elif isinstance(bio_raw, list):
        bio_keywords = [str(x).strip() for x in bio_raw if str(x).strip()] or None
    else:
        bio_keywords = None

    note = payload.get("note", base.get("note"))
    note = str(note).strip() if note else None

    schedule_enabled = bool(payload.get("schedule_enabled", base.get("schedule_enabled", False)))
    schedule_time = payload.get("schedule_time", base.get("schedule_time"))
    if schedule_time:
        schedule_time = str(schedule_time).strip()
        if not re.fullmatch(r"\d{2}:\d{2}", schedule_time):
            raise ValueError("schedule_time must be HH:MM (24-hour UTC)")
    else:
        schedule_time = None

    return {
        "id": base.get("id") or uuid.uuid4().hex[:12],
        "name": name,
        "query": query,
        "max_connects": max_connects,
        "bio_keywords": bio_keywords,
        "note": note,
        "schedule_enabled": schedule_enabled,
        "schedule_time": schedule_time,
        "daily_max": daily_max,
        "enabled": bool(payload.get("enabled", base.get("enabled", True))),
        "created_at": base.get("created_at") or now,
        "updated_at": now,
        "last_run_at": base.get("last_run_at"),
        "last_task_id": base.get("last_task_id"),
        "totals": dict(
            base.get("totals")
            or {"runs": 0, "sent": 0, "skipped": 0}
        ),
        "runs": list(base.get("runs") or [])[:MAX_RUN_HISTORY],
    }


def list_campaigns(user_id: str) -> list[dict[str, Any]]:
    campaigns = _load_campaigns_raw(user_id)
    campaigns.sort(key=lambda c: c.get("updated_at") or "", reverse=True)
    return campaigns


def get_campaign(user_id: str, campaign_id: str) -> dict[str, Any] | None:
    for c in _load_campaigns_raw(user_id):
        if c.get("id") == campaign_id:
            return c
    return None


def create_campaign(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    campaign = _normalize_campaign(payload)
    campaigns = _load_campaigns_raw(user_id)
    campaigns.append(campaign)
    _save_campaigns_raw(user_id, campaigns)
    return campaign


def update_campaign(user_id: str, campaign_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    campaigns = _load_campaigns_raw(user_id)
    for i, existing in enumerate(campaigns):
        if existing.get("id") == campaign_id:
            updated = _normalize_campaign(payload, existing=existing)
            campaigns[i] = updated
            _save_campaigns_raw(user_id, campaigns)
            return updated
    raise KeyError(campaign_id)


def delete_campaign(user_id: str, campaign_id: str) -> bool:
    campaigns = _load_campaigns_raw(user_id)
    next_list = [c for c in campaigns if c.get("id") != campaign_id]
    if len(next_list) == len(campaigns):
        return False
    _save_campaigns_raw(user_id, next_list)
    return True


def _sent_today(campaign: dict[str, Any]) -> int:
    today = datetime.now(timezone.utc).date()
    total = 0
    for run in campaign.get("runs") or []:
        started = run.get("started_at")
        if not started:
            continue
        try:
            dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
        except ValueError:
            continue
        if dt.date() == today:
            total += int(run.get("sent") or 0)
    return total


def _user_has_running_connect(user_id: str) -> bool:
    for task in la.list_tasks(limit=20):
        if task.user_id == user_id and task.action == "connect" and task.is_running():
            return True
    rows = db.list_automation_tasks(limit=10, user_id=user_id)
    for row in rows:
        if row.get("action") == "connect" and row.get("status") == "running":
            return True
    return False


def record_connect_task_start(
    user_id: str, campaign_id: str, task_id: str, *, source: str = "manual"
) -> None:
    """Link a launched connect task to a campaign and append run history."""
    campaigns = _load_campaigns_raw(user_id)
    now = _now_iso()
    found = False
    for i, c in enumerate(campaigns):
        if c.get("id") != campaign_id:
            continue
        runs = list(c.get("runs") or [])
        runs.insert(
            0,
            {
                "task_id": task_id,
                "started_at": now,
                "ended_at": None,
                "status": "running",
                "exit_code": None,
                "sent": 0,
                "skipped": 0,
                "source": source,
            },
        )
        c["runs"] = runs[:MAX_RUN_HISTORY]
        c["last_run_at"] = now
        c["last_task_id"] = task_id
        c["updated_at"] = now
        totals = dict(c.get("totals") or {"runs": 0, "sent": 0, "skipped": 0})
        totals["runs"] = int(totals.get("runs") or 0) + 1
        c["totals"] = totals
        campaigns[i] = c
        found = True
        break
    if found:
        _save_campaigns_raw(user_id, campaigns)
        db.set_config(task_id, campaign_id, TASK_MAP_CATEGORY, user_id=user_id)


def run_campaign(
    user_id: str,
    campaign_id: str,
    *,
    source: str = "manual",
    debug: bool = False,
    headless: bool | None = None,
    no_ai: bool = False,
) -> dict[str, Any]:
    """Launch a connect task from a saved campaign."""
    assert_can_run_automation(user_id)

    campaign = get_campaign(user_id, campaign_id)
    if not campaign:
        raise KeyError(campaign_id)
    if not campaign.get("enabled", True):
        raise ValueError("Campaign is disabled")

    if _user_has_running_connect(user_id):
        raise ValueError("A connect task is already running for this account")

    daily_max = campaign.get("daily_max")
    sent_today = _sent_today(campaign)
    max_connects = int(campaign.get("max_connects") or 10)

    if daily_max is not None:
        remaining = int(daily_max) - sent_today
        if remaining <= 0:
            raise ValueError(
                f"Daily limit reached for this campaign ({daily_max} connects today)"
            )
        max_connects = min(max_connects, remaining)

    params: dict[str, Any] = {
        "query": campaign["query"],
        "max_connects": max_connects,
    }
    if campaign.get("bio_keywords"):
        params["bio_keywords"] = campaign["bio_keywords"]
    if campaign.get("note"):
        params["note"] = campaign["note"]
    if debug:
        params["debug"] = True
    if headless is not None:
        params["headless"] = headless
    if no_ai:
        params["no_ai"] = True

    task = la.start_task("connect", params, user_id=user_id)

    record_connect_task_start(user_id, campaign_id, task.id, source=source)

    return {"task": la.task_to_dict(task, include_log=False), "campaign_id": campaign_id}


def on_connect_task_finished(
    task_id: str,
    user_id: str | None,
    log_path: str | None,
    *,
    status: str | None = None,
    exit_code: int | None = None,
) -> None:
    """Update campaign run history when a connect subprocess ends."""
    if not user_id:
        return

    cfg = db.get_all_by_category(TASK_MAP_CATEGORY, user_id=user_id) or {}
    campaign_id = cfg.get(task_id)
    if not campaign_id:
        return

    sent, skipped = _parse_connect_log(log_path)
    now = _now_iso()
    campaigns = _load_campaigns_raw(user_id)
    for i, c in enumerate(campaigns):
        if c.get("id") != campaign_id:
            continue
        runs = list(c.get("runs") or [])
        for j, run in enumerate(runs):
            if run.get("task_id") == task_id:
                run["ended_at"] = now
                run["status"] = status or run.get("status") or "completed"
                run["exit_code"] = exit_code
                run["sent"] = sent
                run["skipped"] = skipped
                runs[j] = run
                break
        c["runs"] = runs
        totals = dict(c.get("totals") or {"runs": 0, "sent": 0, "skipped": 0})
        totals["sent"] = int(totals.get("sent") or 0) + sent
        totals["skipped"] = int(totals.get("skipped") or 0) + skipped
        c["totals"] = totals
        c["updated_at"] = now
        campaigns[i] = c
        _save_campaigns_raw(user_id, campaigns)
        db.delete_config(task_id, TASK_MAP_CATEGORY, user_id=user_id)
        return


def campaign_history(user_id: str, campaign_id: str) -> list[dict[str, Any]]:
    campaign = get_campaign(user_id, campaign_id)
    if not campaign:
        raise KeyError(campaign_id)
    return list(campaign.get("runs") or [])


def _schedule_due(campaign: dict[str, Any], now: datetime) -> bool:
    if not campaign.get("enabled", True):
        return False
    if not campaign.get("schedule_enabled"):
        return False
    schedule_time = campaign.get("schedule_time")
    if not schedule_time or not re.fullmatch(r"\d{2}:\d{2}", str(schedule_time)):
        return False

    hour, minute = (int(x) for x in str(schedule_time).split(":"))
    # Fire once within the minute window after the scheduled time (UTC).
    if now.hour != hour or now.minute != minute:
        return False

    last_run_at = campaign.get("last_run_at")
    if last_run_at:
        try:
            last_dt = datetime.fromisoformat(str(last_run_at).replace("Z", "+00:00"))
            if last_dt.date() == now.date():
                return False
        except ValueError:
            pass
    return True


def tick_scheduled_campaigns() -> int:
    """Check all users' campaigns and launch any that are due. Returns launch count."""
    launched = 0
    try:
        user_ids = db.list_config_user_ids(CONNECT_CAMPAIGNS_CATEGORY, CAMPAIGNS_KEY)
    except Exception as exc:
        logging.warning("connect_campaigns: could not list users: %s", exc)
        return 0

    now = datetime.now(timezone.utc)
    for user_id in user_ids:
        try:
            for campaign in _load_campaigns_raw(user_id):
                if not _schedule_due(campaign, now):
                    continue
                try:
                    run_campaign(user_id, campaign["id"], source="schedule")
                    launched += 1
                    logging.info(
                        "connect_campaigns: scheduled run user=%s campaign=%s",
                        user_id,
                        campaign.get("name"),
                    )
                except Exception as exc:
                    logging.info(
                        "connect_campaigns: skip scheduled run user=%s campaign=%s: %s",
                        user_id,
                        campaign.get("name"),
                        exc,
                    )
        except Exception as exc:
            logging.warning(
                "connect_campaigns: tick failed user=%s: %s", user_id, exc
            )
    return launched
