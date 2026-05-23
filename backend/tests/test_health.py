from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_status_and_version():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"]
