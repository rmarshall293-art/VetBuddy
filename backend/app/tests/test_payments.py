"""Stripe mock checkout and webhook tests."""

import json

from app.tests.conftest import API, DEFAULT_PASSWORD


def test_checkout_mock(client, veteran_headers):
    response = client.post(
        f"{API}/payments/create-checkout-session",
        headers=veteran_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mock"] is True
    assert body["checkout_url"]
    assert body["session_id"].startswith("cs_test_mock_")


def test_subscription_status_free_tier(client, veteran_headers):
    response = client.get(f"{API}/payments/subscription-status", headers=veteran_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "free"
    assert body["status"] == "active"


def test_webhook_mock_upgrades_subscription(client, veteran_user, db):
    db.commit()
    payload = {
        "id": "evt_test_mock_001",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer_email": veteran_user.email,
                "amount_total": 599,
                "customer": "cus_mock_test",
                "subscription": "sub_mock_test",
            }
        },
    }
    response = client.post(
        f"{API}/payments/webhook",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    login = client.post(
        f"{API}/auth/login",
        json={"email": veteran_user.email, "password": DEFAULT_PASSWORD},
    )
    token = login.json()["access_token"]
    status = client.get(
        f"{API}/payments/subscription-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status.status_code == 200
    assert status.json()["tier"] == "consumer"


def test_webhook_duplicate_idempotent(client, veteran_user, db):
    db.commit()
    payload = {
        "id": "evt_test_mock_dup",
        "type": "checkout.session.completed",
        "data": {"object": {"customer_email": veteran_user.email, "amount_total": 599}},
    }
    first = client.post(
        f"{API}/payments/webhook",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    second = client.post(
        f"{API}/payments/webhook",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
