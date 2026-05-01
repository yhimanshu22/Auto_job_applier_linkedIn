import pytest

def test_get_bot_status(client):
    response = client.get("/api/bot/status")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] in ["stopped", "running", "error"]

def test_bot_runs_history(client, test_db):
    # Insert some mock runs
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
    client.post("/api/bot/stop")
    
    response = client.post("/api/bot/stop")
    assert response.status_code == 200
    assert response.json()["status"] == "not_running"

def test_bot_logs_availability(client):
    response = client.get("/api/bot/logs")
    assert response.status_code == 200
    assert "logs" in response.json()
