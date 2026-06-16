from fastapi.testclient import TestClient
from app_version import get_app_version
from server import app

client = TestClient(app)

def test_health_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "backend"
    assert body["version"] == get_app_version()


def test_version_ok():
    response = client.get("/api/version")
    assert response.status_code == 200
    assert response.json()["version"] == get_app_version()
