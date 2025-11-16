from fastapi.testclient import TestClient

from src.main import app


def test_health_endpoint_returns_success():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "healthy"
