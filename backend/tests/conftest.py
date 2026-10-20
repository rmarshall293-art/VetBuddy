"""Test fixtures: a throwaway PostgreSQL database, migrated, with a real
non-owner login for the API — the same shape as production, synthetic data only.

TEST_DATABASE_ADMIN_URL points at a server where we may create databases
(default: local socket on port 5433). If it is unreachable, database tests are
skipped locally but FAIL when VB_REQUIRE_DB=1 (CI sets it), so a missing
database can never turn into a green build.
"""

from __future__ import annotations

import os
import secrets
import uuid
from datetime import date

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app.config import Settings
from app.db import Database
from app.main import create_app
from app.migrate import migrate

ADMIN_URL = os.environ.get("TEST_DATABASE_ADMIN_URL", "postgresql://postgres@/postgres?host=/tmp&port=5433")
APP_LOGIN = "vetbuddy_api_test"
APP_PASSWORD = "test-only-" + secrets.token_hex(8)
DEV_SECRET = "test-secret-" + "x" * 32
FIXED_TODAY = date(2026, 10, 20)


@pytest.fixture(scope="session")
def database():
    name = "vb_test_" + uuid.uuid4().hex[:10]
    try:
        admin = psycopg.connect(ADMIN_URL, autocommit=True, connect_timeout=3)
    except psycopg.OperationalError as e:
        if os.environ.get("VB_REQUIRE_DB") == "1":
            raise
        pytest.skip(f"PostgreSQL not reachable for tests: {type(e).__name__}")
    admin.execute(f'CREATE DATABASE "{name}"')
    owner_url = make_conninfo(ADMIN_URL, dbname=name)
    migrate(owner_url, APP_LOGIN, APP_PASSWORD)
    app_url = make_conninfo(ADMIN_URL, dbname=name, user=APP_LOGIN, password=APP_PASSWORD)
    yield {"owner_url": owner_url, "app_url": app_url, "name": name}
    admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    admin.close()


@pytest.fixture(scope="session")
def db(database):
    d = Database(database["app_url"], max_size=4)
    yield d
    d.close()


@pytest.fixture
def owner(database):
    """Schema-owner connection (superuser locally) for setup and tamper attempts."""
    with psycopg.connect(database["owner_url"], autocommit=True) as conn:
        yield conn


def dev_settings(**over) -> Settings:
    base = dict(environment="test", app_database_url=None, auth_mode="dev", auth_dev_secret=DEV_SECRET, cors_origins=())
    base.update(over)
    return Settings(**base)


@pytest.fixture
def client(db):
    app = create_app(dev_settings(), db=db, clock=lambda: FIXED_TODAY)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def guest_client():
    """No database, sign-in off: the Launch 0 shape."""
    app = create_app(dev_settings(auth_mode="off"), db=None, clock=lambda: FIXED_TODAY)
    with TestClient(app) as c:
        yield c


class User:
    def __init__(self, client: TestClient, subject: str, tenant: str = "public"):
        self.client = client
        r = client.post("/api/v1/dev/token", json={"subject": subject, "tenant": tenant})
        assert r.status_code == 200, r.text
        self.headers = {"Authorization": "Bearer " + r.json()["access_token"]}

    def get(self, path, **kw):
        return self.client.get(path, headers=self.headers, **kw)

    def post(self, path, **kw):
        return self.client.post(path, headers=self.headers, **kw)

    def patch(self, path, **kw):
        return self.client.patch(path, headers=self.headers, **kw)

    def delete(self, path, **kw):
        return self.client.delete(path, headers=self.headers, **kw)

    def consent(self):
        r = self.post("/api/v1/consents", json={"purpose": "plan_storage"})
        assert r.status_code == 201, r.text
        return self


@pytest.fixture
def make_user(client):
    def _make(tenant: str = "public") -> User:
        return User(client, "synthetic-" + uuid.uuid4().hex[:12], tenant)
    return _make


@pytest.fixture
def second_tenant(owner):
    slug = "org-" + uuid.uuid4().hex[:8]
    owner.execute("INSERT INTO vb.tenants (slug, name) VALUES (%s, %s)", (slug, "Synthetic test organization"))
    return slug


GUARD_PROFILE = {
    "persona": "guard_reserve", "branch": "Army", "component": "national_guard", "legal_authority": "unknown",
    "separation_date": "2027-06-27", "current_jurisdiction": "AL", "destination_jurisdiction": "TX",
    "goals": ["education", "career", "benefits"], "urgency": "30_days",
}

VETERAN_PROFILE = {
    "persona": "veteran", "branch": "Navy", "component": "separated", "separation_date": "2026-09-01",
    "current_jurisdiction": "GA", "goals": ["claims", "housing"], "urgency": "7_days",
}


def table_counts(owner_conn) -> dict[str, int]:
    names = [r[0] for r in owner_conn.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'vb' ORDER BY tablename").fetchall()]
    return {n: owner_conn.execute(f'SELECT count(*) FROM vb."{n}"').fetchone()[0] for n in names}


def conninfo_user(url: str) -> str:
    return conninfo_to_dict(url).get("user", "")
