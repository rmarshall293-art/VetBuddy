"""Shared fixtures for the Benefit Vault tests.

The database fixture builds a throwaway database on the repository's test
PostgreSQL server from the real migration chain (0001-0014) and both seeds,
exactly as scripts/dev_db.sh does, then connects as the owner or as the
application login role vb_app. (The package was first tested against a
sandbox stand-in for 0001-0013; integrated onto slice 03 it runs on the real
schema, so the slice 03 roles, RLS and account deletion are what it sees.)

Connections use app.infra.pg_compat, a psycopg 3 shaped facade over the
repository's libpq driver (ADR 0005). Env: TEST_DATABASE_ADMIN_URL (owner)
and TEST_DATABASE_URL (vb_app), as for the rest of the suite.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))      # backend/
sys.path.insert(0, str(Path(__file__).resolve().parent))          # vault_support

from app.domains.vault.agent import BenefitVaultAgent  # noqa: E402
from app.domains.vault.registry import VaultRegistry, default_registry  # noqa: E402
from app.infra import pg_compat  # noqa: E402
from vault_support import MIGRATIONS, SEEDS, TENANT_A, TENANT_B  # noqa: E402

ADMIN_DSN = os.environ.get("TEST_DATABASE_ADMIN_URL", "host=localhost port=5432 user=postgres dbname=vetbuddy_test")
APP_DSN = os.environ.get("TEST_DATABASE_URL", "host=localhost port=5432 user=vb_app dbname=vetbuddy_test")
DB_PREFIX = "vetbuddy_test_"


@pytest.fixture(scope="session")
def registry() -> VaultRegistry:
    return default_registry()


@pytest.fixture(scope="session")
def dev_agent(registry) -> BenefitVaultAgent:
    """Development environment: publish policy preview_unverified."""
    return BenefitVaultAgent(registry, environment="development")


@pytest.fixture(scope="session")
def prod_agent(registry) -> BenefitVaultAgent:
    """Production environment: publish policy verified_only."""
    return BenefitVaultAgent(registry, environment="production")


def _with_db(dsn: str, dbname: str) -> str:
    parts = [p for p in dsn.split() if not p.startswith("dbname=")]
    return " ".join(parts + [f"dbname={dbname}"])


class Cluster:
    """The repository's test server; logical database names get a test prefix."""

    def _real(self, dbname: str) -> str:
        return dbname if dbname == "postgres" else DB_PREFIX + dbname

    def dsn(self, user: str = "postgres", dbname: str = "vault") -> str:
        if user == "vb_app":
            return _with_db(APP_DSN, self._real(dbname))
        if user != "postgres":
            raise ValueError(f"no test login for {user}")
        return _with_db(ADMIN_DSN, self._real(dbname))

    def connect(self, user: str = "postgres", dbname: str = "vault", autocommit: bool = False):
        return pg_compat.connect(self.dsn(user, dbname), autocommit=autocommit)

    def run_file(self, path: Path, dbname: str = "vault", text: str = None) -> None:
        sql = text if text is not None else path.read_text(encoding="utf-8")
        with self.connect(dbname=dbname) as conn:
            with conn.transaction():
                conn.execute(sql)

    def create_db(self, name: str) -> None:
        with self.connect(dbname="postgres", autocommit=True) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{self._real(name)}" WITH (FORCE)')
            conn.execute(f'CREATE DATABASE "{self._real(name)}"')

    def drop_db(self, name: str) -> None:
        with self.connect(dbname="postgres", autocommit=True) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{self._real(name)}" WITH (FORCE)')

    def build(self, name: str) -> None:
        """A fresh database from the real chain: every migration, then the seeds, each in one transaction."""
        self.create_db(name)
        for path in MIGRATIONS:
            self.run_file(path, dbname=name)
        for path in SEEDS:
            self.run_file(path, dbname=name)


@pytest.fixture(scope="session")
def pg():
    cluster = Cluster()
    try:
        cluster.connect(dbname="postgres").close()
    except pg_compat.Error as exc:
        pytest.skip(f"test PostgreSQL is not reachable: {exc}")
    cluster.build("vault")
    try:
        yield cluster
    finally:
        cluster.drop_db("vault")


@pytest.fixture(scope="session")
def tenants(pg):
    with pg.connect() as conn:
        with conn.transaction():
            for tenant, name in ((TENANT_A, "tenant a"), (TENANT_B, "tenant b")):
                conn.execute("INSERT INTO public.tenant (tenant_id, name, kind) VALUES (%s, %s, 'individual')"
                             " ON CONFLICT DO NOTHING", (tenant, name))
    return TENANT_A, TENANT_B


@pytest.fixture()
def app_conn(pg, tenants):
    """A connection as the application login role (vb_app, member of vetbuddy_app)."""
    conn = pg.connect(user="vb_app")
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture()
def new_tenant(pg):
    """Make a fresh account tenant, so a test owns every row it counts."""
    def make() -> str:
        tenant = str(uuid.uuid4())
        with pg.connect() as conn:
            conn.execute("INSERT INTO public.tenant (tenant_id, name, kind) VALUES (%s, 'test tenant', 'individual')",
                         (tenant,))
        return tenant
    return make
