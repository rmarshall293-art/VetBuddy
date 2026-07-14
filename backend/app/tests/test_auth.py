"""Authentication and RBAC tests."""

from app.core.rbac import Role
from app.tests.conftest import API, DEFAULT_PASSWORD


def test_register_and_login(client, db):
    response = client.post(
        f"{API}/auth/register",
        json={
            "email": "newvet@example.com",
            "password": DEFAULT_PASSWORD,
            "display_name": "New Vet",
            "role": Role.VETERAN.value,
            "preferred_jurisdiction": "AL",
        },
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    login = client.post(
        f"{API}/auth/login",
        json={"email": "newvet@example.com", "password": DEFAULT_PASSWORD},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"


def test_register_rejects_admin_role(client):
    response = client.post(
        f"{API}/auth/register",
        json={
            "email": "badadmin@example.com",
            "password": DEFAULT_PASSWORD,
            "role": Role.SUPER_ADMIN.value,
        },
    )
    assert response.status_code == 400


def test_register_duplicate_email(client, veteran_user, db):
    db.commit()
    response = client.post(
        f"{API}/auth/register",
        json={
            "email": veteran_user.email,
            "password": DEFAULT_PASSWORD,
            "role": Role.VETERAN.value,
        },
    )
    assert response.status_code == 409


def test_refresh_token(client, db):
    reg = client.post(
        f"{API}/auth/register",
        json={
            "email": "refresh@example.com",
            "password": DEFAULT_PASSWORD,
            "role": Role.VETERAN.value,
        },
    )
    refresh_token = reg.json()["refresh_token"]
    response = client.post(f"{API}/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_admin_endpoint_forbidden_for_veteran(client, veteran_headers):
    response = client.get(f"{API}/admin/security-checklist", headers=veteran_headers)
    assert response.status_code == 403


def test_admin_endpoint_allowed_for_admin(client, admin_headers):
    response = client.get(f"{API}/admin/security-checklist", headers=admin_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert any(item["code"] == "audit_logging" for item in items)


def test_unauthenticated_claims_rejected(client):
    response = client.get(f"{API}/claims")
    assert response.status_code == 401


def test_login_invalid_credentials(client, veteran_user, db):
    db.commit()
    response = client.post(
        f"{API}/auth/login",
        json={"email": veteran_user.email, "password": "WrongPassword1!"},
    )
    assert response.status_code == 401
