import glob
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app_paths import get_base_path, get_logs_dir, get_runtime_writable_root
from db_manager import db
from services.linkedin_env import apply_dashboard_linkedin_credentials
from services.plan_limits import PLAN_LIMITS, assert_can_start_bot
from services import supervisor_state as sv

router = APIRouter(prefix="/api/bot", tags=["bot"])


@router.post("/start")
async def start_bot(payload: dict = None):
    user_id = payload.get("user_id", "local-user") if payload else "local-user"

    assert_can_start_bot(user_id)

    if sv.supervisor_process and sv.supervisor_process.poll() is None:
        return {"status": "already_running"}

    try:
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--supervisor"]
        else:
            server_script = os.path.join(get_base_path(), "server.py")
            cmd = [sys.executable, server_script, "--supervisor"]

        cwd = get_runtime_writable_root()
        logging.info(f"Starting supervisor with {cmd} in {cwd}")

        env = os.environ.copy()
        apply_dashboard_linkedin_credentials(env)
        env["USER_ID"] = user_id

        sv.close_supervisor_log()
        logs_dir = get_logs_dir()
        os.makedirs(logs_dir, exist_ok=True)
        console_log = os.path.join(logs_dir, "supervisor-console.log")
        sv.supervisor_log_handle = open(console_log, "a", encoding="utf-8", buffering=1)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sv.supervisor_log_handle.write(
            f"\n{'=' * 60}\n[{ts}] Supervisor session started (API / dashboard)\n{'=' * 60}\n"
        )
        sv.supervisor_log_handle.flush()

        _sup_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        sv.supervisor_process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=sv.supervisor_log_handle,
            stderr=subprocess.STDOUT,
            creationflags=_sup_flags,
        )

        sv.current_run_id = db.start_bot_run(user_id)

        return {"status": "started"}
    except Exception as e:
        sv.close_supervisor_log()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_bot():
    try:
        was_running = sv.supervisor_process is not None and sv.supervisor_process.poll() is None

        if was_running:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(sv.supervisor_process.pid), "/T"],
                    capture_output=True,
                )
            else:
                sv.supervisor_process.terminate()

        sv.supervisor_process = None
        sv.close_supervisor_log()

        if sv.current_run_id:
            db.end_bot_run(sv.current_run_id, 0)
            sv.current_run_id = None

        return {"status": "stopped" if was_running else "not_running"}
    except Exception as e:
        print(f"Error in stop_bot: {e}")
        sv.supervisor_process = None
        sv.current_run_id = None
        sv.close_supervisor_log()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_bot_status(user_id: str = "local-user"):
    subscription = db.get_user_subscription(user_id)
    plan = subscription.get("plan", "free_trial") if subscription else "free_trial"

    if user_id in ["himu09854@gmail.com", "local-user"]:
        plan = "agency"

    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free_trial"])

    stats = db.get_application_stats(user_id)
    applied_count = stats.get("applied", 0)

    status = "stopped"
    if sv.supervisor_process and sv.supervisor_process.poll() is None:
        status = "running"

    activity = db.get_last_activity_snapshot(user_id)

    return {
        "status": status,
        "applied_count": applied_count,
        "limit": limits["monthly_applications"],
        **activity,
    }


@router.get("/logs")
async def get_bot_logs(lines: int = 120):
    lines = max(20, min(int(lines), 500))
    log_dir = get_logs_dir()
    os.makedirs(log_dir, exist_ok=True)

    def tail_file(path: str) -> str:
        if not os.path.isfile(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                buf = f.readlines()
            return "".join(buf[-lines:])
        except Exception as ex:
            return f"(read error: {ex})"

    infra = []
    infra_text_parts = []
    for title, filename in (
        ("Supervisor console (stdout/stderr)", "supervisor-console.log"),
        ("Supervisor", "supervisor.log"),
        ("OpenClaw gateway", "openclaw.log"),
    ):
        path = os.path.join(log_dir, filename)
        chunk = tail_file(path).strip()
        if chunk:
            infra.append({"title": title, "filename": filename, "content": chunk})
            infra_text_parts.append(f"--- {title} ({filename}) ---\n{chunk}")

    profiles = []
    profile_text_parts = []
    for path in sorted(glob.glob(os.path.join(log_dir, "bot-*.txt"))):
        basename = os.path.basename(path)
        inner = basename[len("bot-") : -len(".txt")]
        chunk = tail_file(path).strip()
        profiles.append({"id": inner, "filename": basename, "content": chunk})
        if chunk:
            profile_text_parts.append(f"--- Bot profile {inner} ({basename}) ---\n{chunk}")

    legacy_parts = infra_text_parts + profile_text_parts
    if not legacy_parts:
        msg = (
            "No log files yet. Start the bot from the dashboard to capture supervisor output "
            f"under {log_dir}/."
        )
        return {"logs": msg, "infra": [], "profiles": []}

    return {
        "logs": "\n".join(legacy_parts),
        "infra": infra,
        "profiles": profiles,
    }


@router.get("/runs")
async def get_bot_runs(limit: int = 10):
    runs = db.get_recent_bot_runs(limit)
    return {"runs": runs}


@router.get("/active")
async def get_active_bot_count(user_id: str = "local-user"):
    """Live count of concurrently running bot processes for the billing tile.

    Two sources contribute, deliberately:
      * The job-applier supervisor (this process owns it, so we trust
        ``supervisor_process.poll()`` over the ``bot_runs.status`` column,
        which can lag if the supervisor was killed without ``end_bot_run``).
      * LinkedIn-Automation-Framework subprocesses for the requested user,
        counted via ``AutomationTask.status == 'running'`` — the same number
        the automation dashboard surfaces.

    Returns ``{active, supervisor, automation_tasks, limit, plan}`` so the
    frontend can render ``active / limit`` and optionally break it down.
    """
    automation = int(
        db.get_automation_task_stats(user_id=user_id).get("running", 0)
    )
    supervisor_running = bool(
        sv.supervisor_process and sv.supervisor_process.poll() is None
    )
    supervisor = 1 if supervisor_running else 0

    subscription = db.get_user_subscription(user_id)
    plan = (subscription or {}).get("plan", "free_trial")
    if user_id in ("himu09854@gmail.com", "local-user"):
        plan = "agency"
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free_trial"])

    return {
        "active": supervisor + automation,
        "supervisor": supervisor,
        "automation_tasks": automation,
        "limit": limits["max_active_bots"],
        "plan": plan,
    }
