"""Privacy rights: data export and account deletion (master prompt v6 §3, §4).

Neither needs mission consent: exporting or deleting your data is a right
that survives withdrawing consent. Both run inside the caller's
tenant-scoped transaction like every protected operation.

Scope today: individual (single-person) tenants, which is every account the
app can create. Organization or household tenants need field-level ownership
before either operation can run, and are refused rather than over-deleted.
"""
from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from app.domains.trust.auth import Principal
from app.infra.db import Connection, DatabaseError

EXPORT_SCHEMA = "vetbuddy.account-export.v1"
CONFIRM_PHRASE = "DELETE MY ACCOUNT"


class PrivacyError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        super().__init__(message)
        self.code, self.status = code, status


def _tenant_tables(conn: Connection) -> list[str]:
    rows = conn.query(
        "SELECT c.table_name::text AS t FROM information_schema.columns c "
        "JOIN information_schema.tables it ON it.table_schema = c.table_schema AND it.table_name = c.table_name "
        "WHERE c.table_schema = 'public' AND c.column_name = 'tenant_id' AND it.table_type = 'BASE TABLE' "
        "ORDER BY 1")
    return [r["t"] for r in rows]


def _json(v: Any) -> Any:
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, list):
        return [_json(x) for x in v]
    if isinstance(v, dict):
        return {k: _json(x) for k, x in v.items()}
    return v if not hasattr(v, "as_tuple") else str(v)  # Decimal -> str, never float


def _individual(conn: Connection, p: Principal) -> None:
    t = conn.one("SELECT kind, (SELECT count(*) FROM app_user) AS users FROM tenant WHERE tenant_id = $1", [p.tenant_id])
    if t is None or t["kind"] != "individual" or t["users"] != 1:
        raise PrivacyError("SHARED_ACCOUNT_NOT_SUPPORTED",
                           "This account shares records with others. Export and deletion for shared records "
                           "need per-person ownership, which is not built yet.")


def export_account(conn: Connection, p: Principal, today: dt.date) -> dict:
    """Everything stored for this account, table by table, as plain JSON.
    Generic over tables so a new tenant table is exported automatically."""
    _individual(conn, p)
    tables: dict[str, list[dict]] = {}
    for t in _tenant_tables(conn):
        rows = conn.query(f'SELECT * FROM "{t}" WHERE tenant_id = $1', [p.tenant_id])
        if rows:
            tables[t] = [_json(r) for r in rows]
    return {
        "schema_version": EXPORT_SCHEMA,
        "generated_on": today.isoformat(),
        "account": str(p.user_id),
        "note": "This is everything VetBuddy stores for your account. Integrity fields such as audit hashes are "
                "included so the record is complete.",
        "tables": tables,
    }


def delete_account(conn: Connection, p: Principal, confirm: str) -> dict:
    if confirm != CONFIRM_PHRASE:
        raise PrivacyError("CONFIRMATION_REQUIRED", f'Type "{CONFIRM_PHRASE}" to confirm.', 422)
    _individual(conn, p)
    try:
        row = conn.one("SELECT vb_delete_account($1) AS receipt_id", [p.user_id])
    except DatabaseError as e:
        if e.sqlstate == "0A000":
            raise PrivacyError("SHARED_ACCOUNT_NOT_SUPPORTED", "Shared accounts need per-person deletion.") from e
        raise
    return deletion_status(conn, row["receipt_id"])


def deletion_status(conn: Connection, receipt_id: uuid.UUID) -> dict:
    r = conn.one("SELECT * FROM vb_deletion_status($1)", [receipt_id])
    if r is None:
        raise PrivacyError("NOT_FOUND", "Not found.", 404)
    return {k: _json(v) for k, v in r.items()}
