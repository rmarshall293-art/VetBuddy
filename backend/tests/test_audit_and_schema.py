"""Audit chain integrity, append-only enforcement, schema guards, enum conformance."""

import hashlib
import re

import psycopg
import pytest

from app.kernel import vocab
from conftest import GUARD_PROFILE


def _recompute(row) -> str:
    fields = [row["prev_hash"], str(row["tenant_id"]), row["actor_kind"], str(row["actor_id"] or ""), row["action"],
              row["object_type"], str(row["object_id"] or ""), row["reason_code"] or "", row["trace_id"] or "",
              row["at_utc"]]
    return hashlib.sha256("|".join(fields).encode()).hexdigest()


def test_audit_chain_verifies(make_user, owner):
    u = make_user().consent()
    b = u.post("/api/v1/missions", json=GUARD_PROFILE).json()
    u.patch(f"/api/v1/tasks/{b['tasks'][0]['id']}", json={"status": "done", "expected_version": 1})
    owner.row_factory = psycopg.rows.dict_row
    rows = owner.execute("""SELECT *, to_char(at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') AS at_utc
                              FROM vb.audit_events a WHERE tenant_id = (SELECT id FROM vb.tenants WHERE slug = 'public')
                             ORDER BY seq""").fetchall()
    assert len(rows) >= 3
    prev = "0" * 64
    for r in rows:
        assert r["prev_hash"] == prev and r["hash"] == _recompute(r)
        prev = r["hash"]
    assert {"consent.granted", "mission.created", "task.status_changed"} <= {r["action"] for r in rows}


def test_audit_is_append_only_even_for_owner(make_user, owner):
    make_user().consent()
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        owner.execute("UPDATE vb.audit_events SET action = 'tampered' WHERE seq = (SELECT min(seq) FROM vb.audit_events)")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        owner.execute("DELETE FROM vb.audit_events")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        owner.execute("TRUNCATE vb.audit_events")


def test_audit_and_outbox_carry_no_facts(make_user, owner):
    u = make_user().consent()
    u.post("/api/v1/missions", json={**GUARD_PROFILE, "current_jurisdiction": "WY", "destination_jurisdiction": "VT"})
    blob = str(owner.execute("SELECT array_agg(a::text) FROM vb.audit_events a").fetchone()[0]) + \
        str(owner.execute("SELECT array_agg(o::text) FROM vb.outbox o").fetchone()[0])
    for fact in ("WY", "VT", "national_guard", "Army", "education"):
        assert fact not in blob


def test_no_rls_gaps(owner):
    assert owner.execute("SELECT * FROM vb.rls_gaps()").fetchall() == []


def _check_values(owner, table, column) -> set[str]:
    defs = owner.execute("""SELECT pg_get_constraintdef(c.oid) FROM pg_constraint c
                             JOIN pg_class t ON t.oid = c.conrelid JOIN pg_namespace n ON n.oid = t.relnamespace
                            WHERE n.nspname = 'vb' AND t.relname = %s AND c.contype = 'c'""", (table,)).fetchall()
    for (d,) in defs:
        if f"({column} = " in d or f"({column})::text = " in d or f"{column} = ANY" in d or f"({column})::text = ANY" in d:
            return set(re.findall(r"'([^']+)'::text", d))
    raise AssertionError(f"no CHECK on {table}.{column}")


def test_postgres_checks_match_python_enums(owner):
    from app.api.schemas import TaskUpdate
    task_statuses = set(TaskUpdate.model_fields["status"].annotation.__args__)
    assert _check_values(owner, "tasks", "status") == task_statuses
    assert _check_values(owner, "missions", "privacy_mode") == {"B"}
    assert set(vocab.STAGE_LABELS) >= {"unknown"}


def test_migration_checksums_recorded(owner):
    names = [r[0] for r in owner.execute("SELECT name FROM vb.schema_migrations ORDER BY name").fetchall()]
    assert names[0] == "0001_foundation.sql" and len(names) >= 6
