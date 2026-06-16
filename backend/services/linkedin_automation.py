"""LinkedIn Automation Framework integration.

Spawns the sibling ``linkedin_automation`` package (posting, engagement,
calendar generation, profile pursuit) as isolated subprocesses, with LinkedIn
credentials from the dashboard DB. Session cookies are stored in SQLite
(``user_sessions``) — same table the job-applier bot uses.
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

from app_paths import get_base_path, get_framework_workspace_dir, get_logs_dir
from db_manager import db
from services.linkedin_env import (
    apply_automation_user_credentials,
    apply_dashboard_automation_settings,
)
from services.chrome_profiles import apply_automation_chrome_profile_env


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def get_framework_dir() -> str:
    """Return the cwd for automation subprocesses (writable when packaged)."""
    return get_framework_workspace_dir()


def is_framework_available() -> bool:
    """True when the automation package can be launched on this runtime."""
    if getattr(sys, "frozen", False):
        import importlib.util

        return importlib.util.find_spec("linkedin_automation.__main__") is not None
    framework_dir = get_framework_dir()
    return os.path.isdir(framework_dir) and os.path.isfile(
        os.path.join(framework_dir, "__main__.py")
    )


def _automation_launch_prefix() -> list[str]:
    """Frozen sidecars use ``--automation``; dev uses ``python -m linkedin_automation``."""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--automation"]
    return [sys.executable, "-m", "linkedin_automation"]


# ---------------------------------------------------------------------------
# Task tracking (in-memory)
# ---------------------------------------------------------------------------


@dataclass
class AutomationTask:
    id: str
    action: str
    args: list[str]
    log_path: str
    user_id: str
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


def _build_env(*, user_id: str) -> dict[str, str]:
    """Build the subprocess env: signed-in user creds + framework settings + PYTHONPATH.

    Automation always authenticates as ``user_id`` (session email), not other
    LinkedIn accounts stored in dashboard secrets.

    When the job bot has already logged in, reuses its on-disk Chrome profile
    (``chrome_profiles/{BOT_ID}``). Otherwise falls back to ``user_sessions``
    cookies or a fresh login.
    """
    env = os.environ.copy()
    env["USER_ID"] = user_id
    linkedin_email = apply_automation_user_credentials(env, user_id=user_id)
    apply_automation_chrome_profile_env(
        env, user_id=user_id, linkedin_email=linkedin_email or user_id
    )
    apply_dashboard_automation_settings(env, user_id=user_id)

    # `python -m linkedin_automation` needs the backend root on sys.path so the
    # package can be imported. The subprocess cwd is the package dir itself
    # (so relative paths like `topics.txt`, `logs/`, `static/` resolve as the
    # framework originally expected), which means PYTHONPATH must do the work
    # of pointing Python at the backend root one level above.
    backend_root = get_base_path()
    config_dir = os.path.join(backend_root, "config")
    existing_pp = env.get("PYTHONPATH", "")
    parts = [backend_root, config_dir] + ([existing_pp] if existing_pp else [])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


# ---------------------------------------------------------------------------
# Subprocess launch
# ---------------------------------------------------------------------------


def _build_command(action: str, params: dict[str, Any]) -> list[str]:
    """Map an action + params dict to the framework CLI argv."""
    cmd: list[str] = _automation_launch_prefix() + [action]

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

    elif action == "connect":
        query = params.get("query")
        if not query:
            raise ValueError("connect requires 'query'")
        cmd.append(str(query))
        if params.get("max_connects") is not None:
            cmd += ["--max-connects", str(int(params["max_connects"]))]
        if params.get("note"):
            cmd += ["--note", str(params["note"])]
        if params.get("bio_keywords"):
            cmd += ["--bio-keywords", *map(str, params["bio_keywords"])]

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
    user_id: str,
) -> AutomationTask:
    """Launch a framework subprocess and register it as a tracked task.

    Raises ``FileNotFoundError`` if the framework directory is missing and
    ``ValueError`` for unsupported actions / missing required params.
    """
    if not is_framework_available():
        framework_dir = get_framework_dir()
        raise FileNotFoundError(
            f"LinkedIn automation framework not found at {framework_dir}"
        )
    framework_dir = get_framework_dir()

    cmd = _build_command(action, params)

    task_id = f"la-{action}-{uuid.uuid4().hex[:8]}"
    logs_dir = get_logs_dir()
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, f"linkedin_automation_{task_id}.log")

    env = _build_env(user_id=user_id)
    account_username = (user_id or "").strip() or None

    log_handle = open(log_path, "a", encoding="utf-8", buffering=1)
    env["LINKDAPPLY_AUTOMATION_LOG"] = log_path
    env["PYTHONUNBUFFERED"] = "1"
    ts = _now_iso()
    log_handle.write(f"\n{'=' * 60}\n[{ts}] Task {task_id} started\n")
    log_handle.write(f"Action: {action}\nCommand: {' '.join(cmd)}\nCWD: {framework_dir}\n")
    log_handle.write(f"User: {account_username or '(none)'}\n")
    if env.get("LINKDAPPLY_CHROME_PROFILE_DIR"):
        log_handle.write(f"Chrome profile: {env['LINKDAPPLY_CHROME_PROFILE_DIR']}\n")
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
        args=cmd[len(_automation_launch_prefix()) :],
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
            args=cmd[len(_automation_launch_prefix()) :],
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
        if task.action == "connect":
            try:
                from services.connect_campaigns import on_connect_task_finished

                on_connect_task_finished(
                    task.id,
                    task.user_id,
                    task.log_path,
                    status=task.status,
                    exit_code=task.exit_code,
                )
            except Exception as exc:
                logging.warning(
                    "Could not update connect campaign for task %s: %s",
                    task.id,
                    exc,
                )


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
        return f"(log file not found: {task.log_path})"
    try:
        with open(task.log_path, "r", encoding="utf-8", errors="replace") as f:
            buf = f.readlines()
        text = "".join(buf[-max(20, min(lines, 1000)) :])
        return text or "(log file is empty)"
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


