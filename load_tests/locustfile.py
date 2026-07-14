"""VetBuddy Locust load test scenarios.

Run against a running API (local or staging):

    pip install locust
    locust -f load_tests/locustfile.py --host http://localhost:8000

Headless example:

    locust -f load_tests/locustfile.py --host http://localhost:8000 \\
      --users 50 --spawn-rate 5 --run-time 5m --headless \\
      --html load_tests/reports/latest.html
"""

from __future__ import annotations

import json
import random
import string
from typing import Any

from locust import HttpUser, between, task


API = "/api/v1"
STATES = ["AL", "TX", "FL", "DC", "PR", "CA", "NY", "GA"]
PASSWORD = "LoadTestPass123!"


def _random_email() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"loadtest_{suffix}@example.com"


class VetBuddyUser(HttpUser):
    """Simulates a veteran using VetBuddy — register/login, claims, comparisons."""

    wait_time = between(1, 3)
    access_token: str | None = None

    def on_start(self) -> None:
        self.register_and_login()

    def _auth_headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    def register_and_login(self) -> None:
        email = _random_email()
        payload = {
            "email": email,
            "password": PASSWORD,
            "display_name": "Load Test User",
            "role": "veteran",
            "preferred_jurisdiction": random.choice(STATES),
        }
        with self.client.post(
            f"{API}/auth/register",
            json=payload,
            name="auth/register",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                self.access_token = response.json().get("access_token")
                response.success()
                return
            # Fall back to login if email collision (unlikely)
            response.failure(f"register failed: {response.status_code}")

        with self.client.post(
            f"{API}/auth/login",
            json={"email": email, "password": PASSWORD},
            name="auth/login",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                self.access_token = response.json().get("access_token")
                response.success()
            else:
                response.failure(f"login failed: {response.status_code}")

    @task(3)
    def health(self) -> None:
        self.client.get("/health", name="health")

    @task(5)
    def claims_dashboard(self) -> None:
        headers = self._auth_headers()
        if not headers:
            return
        self.client.get(f"{API}/claims", headers=headers, name="claims/list")
        claim_payload = {
            "title": f"Load test claim {random.randint(1, 9999)}",
            "disclaimer_acknowledged": True,
            "conditions": [{"condition_name": "Tinnitus", "claimed_rating": 10}],
        }
        with self.client.post(
            f"{API}/claims",
            headers=headers,
            json=claim_payload,
            name="claims/create",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"create claim: {response.status_code}")
                return
            claim_id = response.json()["id"]
            response.success()
        self.client.get(
            f"{API}/claims/{claim_id}",
            headers=headers,
            name="claims/get",
        )

    @task(4)
    def state_comparison(self) -> None:
        left, right = random.sample(STATES, 2)
        self.client.get(f"{API}/states", name="states/list")
        self.client.get(
            f"{API}/states/compare",
            params={"from": left, "to": right},
            name="states/compare",
        )
        self.client.post(
            f"{API}/states/compare/custom",
            headers=self._auth_headers(),
            json={
                "from_code": left,
                "to_code": right,
                "metrics": ["va_disability_tax_rule", "ranking_score"],
                "save": bool(self.access_token),
            },
            name="states/compare/custom",
        )

    @task(3)
    def va_mock(self) -> None:
        self.client.get(f"{API}/va/mock/profile", name="va/mock/profile")
        self.client.get(f"{API}/va/mock/claims", name="va/mock/claims")
        self.client.post(
            f"{API}/va/lighthouse/session",
            headers=self._auth_headers(),
            name="va/lighthouse/session",
        )

    @task(2)
    def benefit_search(self) -> None:
        terms = ["education", "property", "tax", "home", "gi bill"]
        self.client.get(
            f"{API}/benefits/search",
            params={"q": random.choice(terms)},
            name="benefits/search",
        )

    @task(2)
    def alabama_ranking(self) -> None:
        self.client.get(f"{API}/alabama/benefits", name="alabama/benefits")
        self.client.get(f"{API}/alabama/ranking", name="alabama/ranking")
        self.client.get(f"{API}/alabama/county-offices", name="alabama/county-offices")


class AnonymousBrowseUser(HttpUser):
    """Unauthenticated browsing — state lists, VA mock, health."""

    wait_time = between(2, 5)
    weight = 1

    @task(5)
    def browse_states(self) -> None:
        self.client.get(f"{API}/states", name="anon/states/list")
        left, right = random.sample(STATES, 2)
        self.client.get(
            f"{API}/states/compare",
            params={"from": left, "to": right},
            name="anon/states/compare",
        )

    @task(3)
    def va_mock_public(self) -> None:
        self.client.get(f"{API}/va/mock/profile", name="anon/va/mock/profile")


class ConcurrentCheckoutUser(HttpUser):
    """Authenticated users exercising payment mock endpoints."""

    wait_time = between(3, 8)
    weight = 1
    access_token: str | None = None

    def on_start(self) -> None:
        email = _random_email()
        reg = self.client.post(
            f"{API}/auth/register",
            json={"email": email, "password": PASSWORD, "role": "veteran"},
            name="payments/register",
        )
        if reg.status_code == 200:
            self.access_token = reg.json().get("access_token")

    @task
    def checkout_flow(self) -> None:
        if not self.access_token:
            return
        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client.get(
            f"{API}/payments/subscription-status",
            headers=headers,
            name="payments/subscription-status",
        )
        self.client.post(
            f"{API}/payments/create-checkout-session",
            headers=headers,
            name="payments/create-checkout-session",
        )
        webhook_body = {
            "id": f"evt_load_{random.randint(1000, 9999)}",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer_email": "load@example.com",
                    "amount_total": 599,
                }
            },
        }
        self.client.post(
            f"{API}/payments/webhook",
            data=json.dumps(webhook_body),
            headers={"Content-Type": "application/json"},
            name="payments/webhook",
        )
