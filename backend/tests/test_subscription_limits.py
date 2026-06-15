import pytest
import subprocess
from datetime import datetime, timedelta


def test_free_trial_user_can_start_bot(client, test_db, monkeypatch, auth_as):
    auth_as("trial-user")
    test_db.set_config("LINKEDIN_USERNAME", "trial@test.com", "secrets", user_id="trial-user")
    test_db.set_config("LINKEDIN_PASSWORD", "secret", "secrets", user_id="trial-user")

    # Mock a trial subscription that expires in 1 hour
    expiry = datetime.utcnow() + timedelta(hours=1)
    test_db.upsert_subscription(
        "trial-user",
        plan="free_trial",
        status="trialing",
        current_period_end=expiry.isoformat(),
    )

    # Mock subprocess.Popen
    class MockProcess:
        pid = 1234
        def poll(self): return None
    
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: MockProcess())

    response = client.post(
        "/api/bot/start",
        json={"user_id": "trial-user"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "started"

def test_expired_trial_cannot_start_bot(client, test_db, auth_as):
    auth_as("expired-user")
    # Mock a trial subscription that expired 1 hour ago
    expiry = datetime.utcnow() - timedelta(hours=1)
    test_db.upsert_subscription(
        "expired-user", 
        plan="free_trial", 
        status="trialing",
        current_period_end=expiry.isoformat()
    )
    
    response = client.post(
        "/api/bot/start",
        json={"user_id": "expired-user"}
    )
    
    assert response.status_code == 402
    assert "expired" in response.json()["detail"].lower()

def test_plan_limits_enforcement(client, test_db, monkeypatch, auth_as):
    auth_as("limit-user")
    test_db.set_config("LINKEDIN_USERNAME", "primary@test.com", "secrets", user_id="limit-user")
    test_db.set_config("LINKEDIN_PASSWORD", "secret", "secrets", user_id="limit-user")
    test_db.set_config("LINKEDIN_USERNAME_1", "extra@test.com", "secrets", user_id="limit-user")
    test_db.set_config("LINKEDIN_PASSWORD_1", "secret", "secrets", user_id="limit-user")

    test_db.upsert_subscription("limit-user", plan="free_trial", status="trialing")
    
    response = client.post(
        "/api/bot/start",
        json={"user_id": "limit-user"}
    )
    
    assert response.status_code == 403
    assert "allows only 1 LinkedIn account(s)" in response.json()["detail"]

def test_subscription_status_includes_cycle(client, test_db, auth_as):
    auth_as("cycle-user")
    test_db.upsert_subscription(
        "cycle-user", 
        plan="pro", 
        billing_cycle="yearly", 
        status="active"
    )
    
    response = client.get("/api/billing/subscription")
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "pro"
    assert data["billing_cycle"] == "yearly"

def test_monthly_limit_enforcement(client, test_db, monkeypatch, auth_as):
    auth_as("starter-user")
    test_db.set_config("LINKEDIN_USERNAME", "starter@test.com", "secrets", user_id="starter-user")
    test_db.set_config("LINKEDIN_PASSWORD", "secret", "secrets", user_id="starter-user")

    # Starter allows 100 applications (based on PLAN_LIMITS)
    test_db.upsert_subscription("starter-user", plan="starter", status="active")
    
    # Log 100 applications for this user
    # Note: db_manager.log_application uses datetime('now') by default
    for _ in range(100):
        test_db.log_application("starter-user", status="applied", job_title="Test", company="Test")
        
    response = client.post(
        "/api/bot/start",
        json={"user_id": "starter-user"}
    )
    
    assert response.status_code == 403
    assert "limit reached" in response.json()["detail"].lower()
