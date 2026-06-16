from unittest.mock import patch

from fastapi.testclient import TestClient


def test_submit_feedback(client: TestClient):
    with patch("routes.feedback.send_feedback_email", return_value=False):
        response = client.post(
            "/api/feedback",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "message": "LinkdApply saved me hours every week applying to roles.",
                "rating": 5,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert isinstance(body["id"], int)
    assert body["email_sent"] is False


def test_submit_feedback_rejects_short_message(client: TestClient):
    response = client.post(
        "/api/feedback",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "message": "short",
        },
    )
    assert response.status_code == 422
