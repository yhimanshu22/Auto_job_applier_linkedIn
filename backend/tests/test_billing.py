from fastapi.testclient import TestClient
from server import app
import pytest

client = TestClient(app)

def test_create_checkout_session_invalid_plan():
    response = client.post(
        "/api/billing/create-checkout-session",
        json={
            "plan": "invalid-plan",
            "user_id": "test-user",
            "email": "test@example.com"
        }
    )
    assert response.status_code == 400
    assert "Invalid plan" in response.json()["detail"]

def test_create_checkout_session_missing_data():
    # Missing plan
    response = client.post(
        "/api/billing/create-checkout-session",
        json={
            "user_id": "test-user",
            "email": "test@example.com"
        }
    )
    assert response.status_code == 422 # Unprocessable Entity for Pydantic validation

def test_stripe_webhook_invalid_signature():
    # Sending a webhook without a valid signature should return 400
    response = client.post(
        "/api/billing/webhook",
        content='{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "invalid"}
    )
    assert response.status_code == 400
