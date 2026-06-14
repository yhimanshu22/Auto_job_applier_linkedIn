import pytest

def test_get_bot_status(client):
    response = client.get("/api/bot/status?user_id=test@example.com")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] in ["stopped", "running", "error"]

def test_bot_runs_history(client, test_db, auth_as):
    auth_as("test-user")
    test_db.start_bot_run("test-user")
    test_db.start_bot_run("test-user")

    response = client.get("/api/bot/runs")
    assert response.status_code == 200
    runs = response.json()["runs"]
    assert len(runs) >= 2
    assert runs[0]["user_id"] == "test-user"

def test_bot_stop_when_not_running(client, monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: None)
    
    # Ensure bot is stopped
    client.post("/api/bot/stop?user_id=test@example.com")
    
    response = client.post("/api/bot/stop?user_id=test@example.com")
    assert response.status_code == 200
    assert response.json()["status"] == "not_running"

def test_bot_logs_availability(client):
    response = client.get("/api/bot/logs?user_id=test@example.com")
    assert response.status_code == 200
    body = response.json()
    assert "logs" in body
    assert "log_dir" in body
    assert "files" in body


def test_bot_active_zero_when_idle(client):
    """No supervisor process and no running automation tasks → active == 0."""
    res = client.get("/api/bot/active?user_id=himu09854@gmail.com")
    assert res.status_code == 200
    body = res.json()
    assert body["active"] == 0
    assert body["supervisor"] == 0
    assert body["automation_tasks"] == 0
    assert body["plan"] == "agency"
    assert body["limit"] >= 1


def test_bot_active_counts_running_automation_tasks(client, test_db, auth_as):
    """Running automation tasks should bump the active count."""
    auth_as("active-user")
    test_db.create_automation_task(
        "active-task-1", "post", ["arg"], "/log", user_id="active-user"
    )
    test_db.create_automation_task(
        "active-task-2", "engage", ["arg"], "/log", user_id="active-user"
    )
    # A finished task must NOT count.
    test_db.create_automation_task(
        "done-task", "pursue", ["arg"], "/log", user_id="active-user"
    )
    test_db.finalize_automation_task("done-task", exit_code=0)

    res = client.get("/api/bot/active")
    assert res.status_code == 200
    body = res.json()
    assert body["automation_tasks"] == 2
    assert body["active"] == 2  # no supervisor running in tests
    assert body["supervisor"] == 0


def test_bot_active_includes_supervisor(client, monkeypatch):
    """When the supervisor process is alive, supervisor counts as 1 bot."""
    from services import supervisor_state as sv

    class _FakeProc:
        pid = 9999
        def poll(self):
            return None  # still running

    monkeypatch.setattr(sv, "supervisor_process", _FakeProc())
    try:
        res = client.get("/api/bot/active?user_id=test@example.com")
        assert res.status_code == 200
        body = res.json()
        assert body["supervisor"] == 1
        assert body["active"] >= 1
    finally:
        monkeypatch.setattr(sv, "supervisor_process", None)
