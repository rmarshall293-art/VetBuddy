"""Append-only, per-tenant hash-chained audit trail.

Each row's row_hash = sha256(prev_hash | action | resource | resource_id |
canonical(new_value) | reason). A per-tenant transaction advisory lock
serializes writers so the chain cannot fork. audit_event has an
UPDATE/DELETE-forbidding trigger (0008) and the app role holds no UPDATE
grant on it (0009). Values passed here must be references/enums, not PII.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from app.infra.db import Connection


def record(conn: Connection, tenant_id: uuid.UUID, actor_user_id: uuid.UUID | None, action: str,
           resource_type: str, resource_id: uuid.UUID | None, new_value: dict[str, Any] | None = None,
           reason: str | None = None) -> str:
    conn.query("SELECT pg_advisory_xact_lock(hashtext($1))", [f"audit:{tenant_id}"])
    prev = conn.one(
        "SELECT row_hash FROM audit_event WHERE tenant_id = $1 ORDER BY created_at DESC, audit_id DESC LIMIT 1",
        [tenant_id],
    )
    prev_hash = prev["row_hash"] if prev else "GENESIS"
    canonical = json.dumps(new_value or {}, sort_keys=True, default=str)
    row_hash = hashlib.sha256(
        "|".join([prev_hash, action, resource_type, str(resource_id or ""), canonical, reason or ""]).encode()
    ).hexdigest()
    conn.query(
        "INSERT INTO audit_event (tenant_id, actor_user_id, action, resource_type, resource_id, new_value, reason,"
        " prev_hash, row_hash, created_at) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9, clock_timestamp())",
        [tenant_id, actor_user_id, action, resource_type, resource_id, new_value, reason, prev_hash, row_hash],
    )
    return row_hash


def verify_chain(conn: Connection, tenant_id: uuid.UUID) -> bool:
    rows = conn.query(
        "SELECT action, resource_type, resource_id, new_value, reason, prev_hash, row_hash FROM audit_event"
        " WHERE tenant_id = $1 ORDER BY created_at, audit_id", [tenant_id])
    prev = "GENESIS"
    for r in rows:
        if r["prev_hash"] != prev:
            return False
        canonical = json.dumps(r["new_value"] or {}, sort_keys=True, default=str)
        expect = hashlib.sha256("|".join([prev, r["action"], r["resource_type"], str(r["resource_id"] or ""),
                                          canonical, r["reason"] or ""]).encode()).hexdigest()
        if expect != r["row_hash"]:
            return False
        prev = r["row_hash"]
    return True
