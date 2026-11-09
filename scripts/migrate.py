#!/usr/bin/env python3
"""Apply database/migrations/*.sql in order, once each, recording a sha256
per file. Refuses to continue if an already-applied file has changed
(migrations are append-only; fix forward with a new file).

Usage: DATABASE_ADMIN_URL=postgresql://... python3 scripts/migrate.py
The admin URL must be the schema owner. The API never uses this URL.
"""
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.infra.db import connect  # noqa: E402

MIGRATIONS = ROOT / "database" / "migrations"


def main() -> int:
    dsn = os.environ.get("DATABASE_ADMIN_URL")
    if not dsn:
        print("DATABASE_ADMIN_URL is not set", file=sys.stderr)
        return 2
    with connect(dsn) as conn:
        conn.execute_script(
            "CREATE TABLE IF NOT EXISTS schema_migration ("
            " filename TEXT PRIMARY KEY, sha256 TEXT NOT NULL,"
            " applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        applied = {r["filename"]: r["sha256"] for r in conn.query("SELECT filename, sha256 FROM schema_migration")}
        for path in sorted(MIGRATIONS.glob("*.sql")):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if path.name in applied:
                if applied[path.name] != digest:
                    print(f"REFUSING: {path.name} changed after it was applied", file=sys.stderr)
                    return 1
                continue
            print(f"applying {path.name}")
            conn.execute_script("BEGIN;\n" + path.read_text() + "\nCOMMIT;")
            conn.query("INSERT INTO schema_migration (filename, sha256) VALUES ($1, $2)", [path.name, digest])
    print("migrations up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
