from fastapi.testclient import TestClient
from server import app
import pytest
import os
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_create_checkout_session_valid_monthly():
    with patch("stripe.checkout.Session.create") as mock_stripe:
        mock_stripe.return_value = MagicMock(url="https://checkout.stripe.com/test")
        
        response = client.post(
            "/api/billing/create-checkout-session",
            json={
                "plan": "pro",
                "billing_cycle": "monthly",
                "user_id": "test-user",
                "email": "test@example.com"
            }
        )
        assert response.status_code == 200
        assert response.json()["url"] == "https://checkout.stripe.com/test"
        
        # Verify metadata sent to Stripe
        args, kwargs = mock_stripe.call_args
        assert kwargs["metadata"]["billing_cycle"] == "monthly"
        assert kwargs["metadata"]["plan"] == "pro"

def test_create_checkout_session_valid_yearly():
    with patch("stripe.checkout.Session.create") as mock_stripe:
        mock_stripe.return_value = MagicMock(url="https://checkout.stripe.com/test-annual")
        
        response = client.post(
            "/api/billing/create-checkout-session",
            json={
                "plan": "agency",
                "billing_cycle": "yearly",
                "user_id": "test-user",
                "email": "test@example.com"
            }
        )
        assert response.status_code == 200
        assert response.json()["url"] == "https://checkout.stripe.com/test-annual"
        
        args, kwargs = mock_stripe.call_args
        assert kwargs["metadata"]["billing_cycle"] == "yearly"

def test_create_checkout_session_invalid_plan():
    response = client.post(
        "/api/billing/create-checkout-session",
        json={
            "plan": "invalid-plan",
            "billing_cycle": "monthly",
            "user_id": "test-user",
            "email": "test@example.com"
        }
    )
    # Pydantic Literal check will return 422
    assert response.status_code == 422

def test_create_checkout_session_invalid_cycle():
    response = client.post(
        "/api/billing/create-checkout-session",
        json={
            "plan": "pro",
            "billing_cycle": "daily", # Invalid literal
            "user_id": "test-user",
            "email": "test@example.com"
        }
    )
    assert response.status_code == 422

def test_start_free_trial_success():
    # Use a fresh user ID
    user_id = "new-trial-user"
    response = client.post(
        "/api/billing/start-free-trial",
        json={"user_id": user_id}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "expires_at" in response.json()

def test_start_free_trial_duplicate_prevented():
    user_id = "existing-trial-user"
    # First time
    client.post("/api/billing/start-free-trial", json={"user_id": user_id})
    
    # Second time
    response = client.post("/api/billing/start-free-trial", json={"user_id": user_id})
    assert response.status_code == 400
    assert "already used your trial" in response.json()["detail"]

def test_stripe_webhook_invalid_signature():
    response = client.post(
        "/api/billing/webhook",
        content='{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "invalid"}
    )
    assert response.status_code == 400
