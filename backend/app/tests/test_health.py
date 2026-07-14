"""Health endpoint tests."""

from app.tests.conftest import API


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["va_mode"] == "mock"
    assert body["stripe_mode"] == "mock"


def test_health_api_prefix(client):
    response = client.get(f"{API}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
