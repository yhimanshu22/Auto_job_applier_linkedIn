import hashlib
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from server import app
from services import payu as payu_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def _billing_session(auth_as):
    auth_as("test-user")


@pytest.fixture(autouse=True)
def _payu_env(monkeypatch):
    monkeypatch.setenv("PAYU_MERCHANT_KEY", "gtKFFx")
    monkeypatch.setenv("PAYU_MERCHANT_SALT", "eCwWELxi")
    monkeypatch.setenv("PAYU_ENV", "test")
    monkeypatch.setenv("BACKEND_PUBLIC_URL", "http://127.0.0.1:8000")


def test_generate_request_hash_is_deterministic():
    params = {
        "key": "gtKFFx",
        "txnid": "LA123",
        "amount": "1599.00",
        "productinfo": "LinkdApply Starter Monthly",
        "firstname": "Test",
        "email": "test@example.com",
        "udf1": "user@example.com",
        "udf2": "starter",
        "udf3": "monthly",
    }
    salt = "eCwWELxi"
    first = payu_service.generate_request_hash(params, salt)
    second = payu_service.generate_request_hash(params, salt)
    assert first == second
    assert len(first) == 128


def test_verify_response_hash_roundtrip():
    params = {
        "key": "gtKFFx",
        "txnid": "LA123",
        "amount": "1599.00",
        "productinfo": "LinkdApply Starter Monthly",
        "firstname": "Test",
        "email": "test@example.com",
        "udf1": "user@example.com",
        "udf2": "starter",
        "udf3": "monthly",
        "status": "success",
    }
    salt = "eCwWELxi"
    reverse_string = (
        f"{salt}|success||||||"
        f"{params['udf5'] if 'udf5' in params else ''}|"
        f"{params.get('udf4', '')}|{params.get('udf3', '')}|{params.get('udf2', '')}|"
        f"{params.get('udf1', '')}|{params['email']}|{params['firstname']}|"
        f"{params['productinfo']}|{params['amount']}|{params['txnid']}|{params['key']}"
    )
    params["hash"] = hashlib.sha512(reverse_string.encode("utf-8")).hexdigest().lower()
    assert payu_service.verify_response_hash(params, salt)


def test_payu_checkout_page_returns_auto_submit_form():
    response = client.get(
        "/api/billing/payu/checkout-page",
        params={
            "plan": "starter",
            "billing_cycle": "monthly",
            "user_id": "test-user",
            "email": "test@example.com",
            "firstname": "Test",
        },
    )
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert 'action="https://test.payu.in/_payment"' in body
    assert 'name="hash"' in body
    assert 'document.forms.payu.submit()' in body
    assert "1599.00" in body


def test_payu_initiate_returns_checkout_payload():
    response = client.post(
        "/api/billing/payu/initiate",
        json={
            "plan": "starter",
            "billing_cycle": "monthly",
            "user_id": "test-user",
            "email": "test@example.com",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "https://test.payu.in/_payment"
    assert data["params"]["amount"] == "1599.00"
    assert data["params"]["udf2"] == "starter"
    assert data["params"]["hash"]


def test_payu_initiate_not_configured(monkeypatch):
    monkeypatch.delenv("PAYU_MERCHANT_KEY", raising=False)
    response = client.post(
        "/api/billing/payu/initiate",
        json={
            "plan": "starter",
            "billing_cycle": "monthly",
            "user_id": "test-user",
            "email": "test@example.com",
        },
    )
    assert response.status_code == 503


def test_payu_success_callback_activates_subscription(test_db):
    params = {
        "key": os.environ["PAYU_MERCHANT_KEY"],
        "txnid": "LA999",
        "amount": "1599.00",
        "productinfo": "LinkdApply Starter Monthly",
        "firstname": "Test",
        "email": "test@example.com",
        "udf1": "payu-callback-user",
        "udf2": "starter",
        "udf3": "monthly",
        "status": "success",
    }
    salt = os.environ["PAYU_MERCHANT_SALT"]
    reverse_string = (
        f"{salt}|success||||||"
        f"{params.get('udf5', '')}|{params.get('udf4', '')}|{params.get('udf3', '')}|"
        f"{params.get('udf2', '')}|{params.get('udf1', '')}|{params['email']}|"
        f"{params['firstname']}|{params['productinfo']}|{params['amount']}|"
        f"{params['txnid']}|{params['key']}"
    )
    params["hash"] = hashlib.sha512(reverse_string.encode("utf-8")).hexdigest().lower()

    with patch("services.payu.verify_payment_with_payu", return_value={"status": "success"}):
        response = client.post("/api/billing/payu/callback/success", data=params, follow_redirects=False)

    assert response.status_code == 303
    assert "billing/success" in response.headers["location"]
    sub = test_db.get_user_subscription("payu-callback-user")
    assert sub is not None
    assert sub["plan"] == "starter"
    assert sub["payment_provider"] == "payu"
    assert sub["status"] == "active"
