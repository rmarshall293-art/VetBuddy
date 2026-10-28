"""Shared fixtures. Synthetic data only. Requires a migrated test database:
    VB_DB=vetbuddy_test scripts/dev_db.sh --reset
Env:
    TEST_DATABASE_URL        app role (vb_app) DSN
    TEST_DATABASE_ADMIN_URL  owner DSN, used ONLY to set up / inspect fixtures
"""
import datetime as dt
import os
import unittest

from starlette.testclient import TestClient

from app.api.main import create_app
from app.infra import config
from app.infra.db import connect

APP_DSN = os.environ.get("TEST_DATABASE_URL", "host=localhost port=5432 user=vb_app dbname=vetbuddy_test")
ADMIN_DSN = os.environ.get("TEST_DATABASE_ADMIN_URL", "host=localhost port=5432 user=postgres dbname=vetbuddy_test")
TODAY = dt.date(2026, 10, 20)

ONBOARD = dict(persona="guard_reserve", branch="Army", component="national_guard", legal_authority="unknown",
               separation_date="2027-06-30", current_jurisdiction="AL", destination_jurisdiction="TX",
               goals=["education", "career", "benefits"], urgency="30_days", consent=True)


def settings(**overrides) -> config.Settings:
    base = dict(database_url=APP_DSN, auth_mode="dev", dev_token_secret=b"test-secret-not-real",
                mode_c_enabled=False, web_dir=config.ROOT / "web")
    base.update(overrides)
    return config.Settings(**base)


class ApiCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(settings(), clock=lambda: TODAY)
        cls.client = TestClient(cls.app)

    def signup(self) -> dict:
        r = self.client.post("/api/v1/dev/signup")
        self.assertEqual(r.status_code, 201, r.text)
        return {"authorization": "Bearer " + r.json()["token"]}

    def onboard(self, headers, **overrides) -> str:
        r = self.client.post("/api/v1/onboarding", json={**ONBOARD, **overrides}, headers=headers)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["mission_id"]


def admin():
    return connect(ADMIN_DSN)
