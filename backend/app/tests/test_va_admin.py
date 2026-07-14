"""VA mock integration and admin checklist tests."""

from app.tests.conftest import API


def test_va_mock_profile(client):
    response = client.get(f"{API}/va/mock/profile")
    assert response.status_code == 200
    body = response.json()
    assert "name" in body or "firstName" in body or "data_status" in body


def test_va_mock_claims(client):
    response = client.get(f"{API}/va/mock/claims")
    assert response.status_code == 200
    body = response.json()
    assert body["data_status"] == "mock"
    assert isinstance(body["claims"], list)
    assert len(body["claims"]) >= 1


def test_va_lighthouse_session(client, veteran_headers):
    response = client.post(f"{API}/va/lighthouse/session", headers=veteran_headers)
    assert response.status_code == 200
    body = response.json()
    assert body.get("mode") == "mock" or body.get("mock") is True or "authorization_url" in body


def test_admin_legal_readiness(client, admin_headers):
    response = client.get(f"{API}/admin/legal-readiness", headers=admin_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 5
    codes = {item["code"] for item in items}
    assert "privacy_policy" in codes
    assert "terms_of_service" in codes


def test_admin_update_security_checklist(client, admin_headers):
    listing = client.get(f"{API}/admin/security-checklist", headers=admin_headers)
    assert listing.status_code == 200
    item = listing.json()[0]
    updated = client.patch(
        f"{API}/admin/security-checklist/{item['id']}",
        headers=admin_headers,
        json={"status": "in_progress", "notes": "CI test update"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"


def test_benefits_search_empty(client):
    response = client.get(f"{API}/benefits/search", params={"q": "education"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
