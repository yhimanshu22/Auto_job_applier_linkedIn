from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_health_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "backend"

def test_version_ok():
    response = client.get("/api/version")
    assert response.status_code == 200
    assert "version" in response.json()
