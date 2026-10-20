"""Apply backend/migrations/*.sql in order, once each, recording checksums.

    DATABASE_URL=postgresql://owner@host/db python -m app.migrate

Forward-only and non-destructive: an applied migration whose file has changed
is an error, never silently re-run. Optional: APP_DB_LOGIN / APP_DB_PASSWORD
create (or update) the API's login role as a member of vetbuddy_app.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import psycopg
from psycopg import sql

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def migrate(url: str, app_login: str | None = None, app_password: str | None = None) -> list[str]:
    applied_now = []
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS vb")
        conn.execute("""CREATE TABLE IF NOT EXISTS vb.schema_migrations (
            name text PRIMARY KEY, checksum text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())""")
        done = dict(conn.execute("SELECT name, checksum FROM vb.schema_migrations").fetchall())
        for path in sorted(MIGRATIONS.glob("*.sql")):
            body = path.read_text()
            checksum = hashlib.sha256(body.encode()).hexdigest()
            if path.name in done:
                if done[path.name] != checksum:
                    raise RuntimeError(f"{path.name} changed after it was applied; write a new migration instead")
                continue
            with conn.transaction():
                conn.execute(body)
                conn.execute("INSERT INTO vb.schema_migrations (name, checksum) VALUES (%s, %s)", (path.name, checksum))
            applied_now.append(path.name)
        if app_login:
            exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (app_login,)).fetchone()
            verb = sql.SQL("ALTER") if exists else sql.SQL("CREATE")
            stmt = sql.SQL("{} ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS").format(verb, sql.Identifier(app_login))
            if app_password:
                stmt += sql.SQL(" PASSWORD {}").format(sql.Literal(app_password))
            conn.execute(stmt)
            conn.execute(sql.SQL("GRANT vetbuddy_app TO {}").format(sql.Identifier(app_login)))
    return applied_now


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2
    names = migrate(url, os.environ.get("APP_DB_LOGIN"), os.environ.get("APP_DB_PASSWORD"))
    print("applied: " + (", ".join(names) if names else "nothing (up to date)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
