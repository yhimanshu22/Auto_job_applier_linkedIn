"""Start/stop the dashboard-spawned job-applier supervisor and its process tree."""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys

from services import supervisor_state as sv

logger = logging.getLogger(__name__)


def supervisor_popen_kwargs() -> dict:
    """Isolate the supervisor in its own process group so stop kills the full tree."""
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        return {"creationflags": flags} if flags else {}
    return {"start_new_session": True}


def stop_supervisor(*, reason: str = "api") -> bool:
    """Terminate the supervisor and all child bot/Chrome processes. Returns True if one was running."""
    proc = sv.supervisor_process
    was_running = proc is not None and proc.poll() is None

    if not was_running:
        sv.supervisor_process = None
        sv.close_supervisor_log()
        return False

    pid = proc.pid
    logger.info("Stopping job-applier supervisor (pid=%s, reason=%s)", pid, reason)

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid), "/T"],
                capture_output=True,
                check=False,
            )
        else:
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                proc.terminate()
            try:
                proc.wait(timeout=12)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except ProcessLookupError:
                    proc.kill()
    except Exception:
        logger.exception("Failed to stop supervisor pid=%s", pid)

    sv.supervisor_process = None
    sv.close_supervisor_log()
    return True
