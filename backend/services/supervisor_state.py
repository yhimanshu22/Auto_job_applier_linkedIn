"""Process handles for the dashboard-spawned supervisor (single orchestrator)."""

supervisor_process = None
current_run_id = None
supervisor_log_handle = None


def close_supervisor_log() -> None:
    global supervisor_log_handle
    if supervisor_log_handle:
        try:
            supervisor_log_handle.flush()
            supervisor_log_handle.close()
        except Exception:
            pass
        supervisor_log_handle = None
