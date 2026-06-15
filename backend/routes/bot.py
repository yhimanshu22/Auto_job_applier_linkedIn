import logging
import os
import subprocess
import sys

from fastapi import APIRouter, HTTPException, Request

from app_paths import get_runtime_writable_root, subprocess_env
from db_manager import db
from services.linkedin_env import apply_dashboard_linkedin_credentials
from services.admin import effective_plan
from services.plan_limits import PLAN_LIMITS, assert_can_start_bot
from services import supervisor_state as sv
from services.bot_supervisor import stop_supervisor, supervisor_popen_kwargs
from utils.debug_logs import (
    SUPERVISOR_CONSOLE_LOG,
    append_session_marker,
    collect_bot_logs_payload,
    run_has_logs,
    scoped_log_path,
)
from utils.user_resolution import resolve_user_id

router = APIRouter(prefix="/api/bot", tags=["bot"])


@router.post("/start")
async def start_bot(request: Request, payload: dict = None):
    claimed = payload.get("user_id") if payload else None
    user_id = await resolve_user_id(request, claimed)

    assert_can_start_bot(user_id)

    if sv.supervisor_process and sv.supervisor_process.poll() is None:
        return {"status": "already_running"}

    try:
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--supervisor"]
        else:
            from app_paths import get_base_path

            server_script = os.path.join(get_base_path(), "server.py")
            cmd = [sys.executable, server_script, "--supervisor"]

        cwd = get_runtime_writable_root()
        logging.info(f"Starting supervisor with {cmd} in {cwd}")

        env = subprocess_env()
        apply_dashboard_linkedin_credentials(env, user_id=user_id)
        env["USER_ID"] = user_id

        run_id = db.start_bot_run(user_id)
        sv.current_run_id = run_id
        env["BOT_RUN_ID"] = str(run_id)

        sv.close_supervisor_log()
        console_log = scoped_log_path(SUPERVISOR_CONSOLE_LOG)
        os.makedirs(os.path.dirname(console_log), exist_ok=True)
        sv.supervisor_log_handle = open(console_log, "a", encoding="utf-8", buffering=1)
        append_session_marker(
            console_log, f"Supervisor session started (run #{run_id}, API / dashboard)"
        )

        sv.supervisor_process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=sv.supervisor_log_handle,
            stderr=subprocess.STDOUT,
            **supervisor_popen_kwargs(),
        )

        return {"status": "started", "run_id": run_id}
    except Exception as e:
        sv.close_supervisor_log()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_bot(request: Request, user_id: str | None = None):
    await resolve_user_id(request, user_id)
    try:
        was_running = stop_supervisor(reason="dashboard")
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
async def get_bot_status(request: Request, user_id: str | None = None):
    user_id = await resolve_user_id(request, user_id)
    subscription = db.get_user_subscription(user_id)
    plan = subscription.get("plan", "free_trial") if subscription else "free_trial"

    plan = effective_plan(user_id, plan)

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
async def get_bot_logs(
    request: Request,
    lines: int = 120,
    user_id: str | None = None,
    run_id: int | None = None,
):
    await resolve_user_id(request, user_id)
    resolved_run = run_id
    if resolved_run is None and sv.current_run_id:
        resolved_run = sv.current_run_id
    return collect_bot_logs_payload(lines=lines, run_id=resolved_run)


@router.get("/runs")
async def get_bot_runs(request: Request, user_id: str | None = None, limit: int = 10):
    user_id = await resolve_user_id(request, user_id)
    runs = db.get_recent_bot_runs(limit, user_id=user_id)
    enriched = []
    for row in runs:
        item = dict(row)
        item["has_logs"] = run_has_logs(row["id"])
        enriched.append(item)
    return {"runs": enriched}


@router.get("/active")
async def get_active_bot_count(request: Request, user_id: str | None = None):
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
    user_id = await resolve_user_id(request, user_id)
    automation = int(
        db.get_automation_task_stats(user_id=user_id).get("running", 0)
    )
    supervisor_running = bool(
        sv.supervisor_process and sv.supervisor_process.poll() is None
    )
    supervisor = 1 if supervisor_running else 0

    subscription = db.get_user_subscription(user_id)
    plan = (subscription or {}).get("plan", "free_trial")
    plan = effective_plan(user_id, plan)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free_trial"])

    return {
        "active": supervisor + automation,
        "supervisor": supervisor,
        "automation_tasks": automation,
        "limit": limits["max_active_bots"],
        "plan": plan,
    }
