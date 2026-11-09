"""Database access for the vault's tenant tables (migration 0014).

Every call runs inside a transaction with ``vetbuddy.tenant_id`` set locally,
so row-level security scopes it to one tenant. The app role holds no DELETE
grant: grants are revoked (an UPDATE of ``revoked_at`` only), saved benefits
are removed through ``public.vb_vault_discard`` (migration 0014), and the ledger is append-only
(the database assigns its sequence and hashes).

The store implements the same interfaces as the in-memory grant store and
ledger, so the broker runs unchanged against either.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Iterable, List, Optional

from .governance.grants import PullGrant
from .governance.ledger import LedgerEntry, validate_fields, verify_chain
from .registry import Review
from .vocab import ALLOW_REASON, SAVED_STATUSES

DISCARD_KINDS = ("saved_benefit", "grant")


class StoreError(RuntimeError):
    pass


def _uuid(value) -> Optional[str]:
    """The canonical spelling of a UUID, or None when the value is not one."""
    if not isinstance(value, str):
        return None
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _tenant(tenant_ref: str) -> str:
    tenant = _uuid(tenant_ref)
    if tenant is None:
        raise StoreError("an account tenant is a UUID")
    return tenant


class VaultStore:
    """Either one long-lived connection (tests, scripts) or a connection factory:
    with ``connect``, every operation opens its own connection and transaction
    and closes it (the API builds one store per request, so ``self.conn`` is
    never shared between requests)."""

    def __init__(self, conn=None, *, connect=None):
        if (conn is None) == (connect is None):
            raise ValueError("give a connection or a connection factory")
        self.conn, self._connect = conn, connect

    def _run(self, tenant_ref: str, fn):
        tenant = _tenant(tenant_ref)
        if self._connect is None:
            return self._in_transaction(tenant, fn)
        with self._connect() as conn:
            self.conn = conn
            try:
                return self._in_transaction(tenant, fn)
            finally:
                self.conn = None

    def _in_transaction(self, tenant: str, fn):
        with self.conn.transaction():
            self.conn.execute("SELECT set_config('vetbuddy.tenant_id', %s, true)", (tenant,))
            return fn(tenant)

    # ── grants ─────────────────────────────────────────────────────────────
    @staticmethod
    def _grant(row) -> PullGrant:
        return PullGrant(grant_id=str(row[0]), tenant_ref=str(row[1]), grantee=row[2], source_agent=row[3],
                         fact_keys=frozenset(row[4]), purpose=row[5], mode=row[6], scope="account",
                         granted_at=row[7], expires_at=row[8], revoked_at=row[9])

    _GRANT_COLS = ("grant_id, tenant_id, grantee, source_agent, fact_keys, purpose, mode, granted_at, "
                   "expires_at, revoked_at")

    def add(self, grant: PullGrant) -> PullGrant:
        if grant.mode != "B" or grant.scope != "account":
            raise StoreError("only Mode B account grants are stored")

        def go(tenant):
            row = self.conn.execute(
                f"INSERT INTO public.vault_pull_grant (grant_id, tenant_id, grantee, source_agent, fact_keys, purpose,"
                f" mode, granted_at, expires_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING {self._GRANT_COLS}",
                (grant.grant_id, tenant, grant.grantee, grant.source_agent, sorted(grant.fact_keys), grant.purpose,
                 grant.mode, grant.granted_at, grant.expires_at)).fetchone()
            return self._grant(row)
        return self._run(grant.tenant_ref, go)

    def revoke(self, tenant_ref: str, grant_id: str, now: datetime) -> Optional[PullGrant]:
        """Revoke once; a second call returns the grant as first revoked. None when there is no such grant."""
        gid = _uuid(grant_id)

        def go(tenant):
            if gid is None:
                return None
            self.conn.execute(
                "UPDATE public.vault_pull_grant SET revoked_at = %s WHERE grant_id = %s AND revoked_at IS NULL",
                (now, gid))
            row = self.conn.execute(f"SELECT {self._GRANT_COLS} FROM public.vault_pull_grant WHERE grant_id = %s",
                                    (gid,)).fetchone()
            return self._grant(row) if row else None
        return self._run(tenant_ref, go)

    def for_source(self, tenant_ref: str, source_agent: str, purpose: str) -> List[PullGrant]:
        def go(tenant):
            rows = self.conn.execute(
                f"SELECT {self._GRANT_COLS} FROM public.vault_pull_grant WHERE source_agent = %s AND purpose = %s"
                " ORDER BY granted_at, grant_id", (source_agent, purpose)).fetchall()
            return [self._grant(r) for r in rows]
        return self._run(tenant_ref, go)

    def list(self, tenant_ref: str) -> List[PullGrant]:
        def go(tenant):
            rows = self.conn.execute(f"SELECT {self._GRANT_COLS} FROM public.vault_pull_grant"
                                     " ORDER BY granted_at, grant_id").fetchall()
            return [self._grant(r) for r in rows]
        return self._run(tenant_ref, go)

    # ── ledger ─────────────────────────────────────────────────────────────
    _LEDGER_COLS = ("seq, tenant_id, occurred_at, event, requester, source_agent, purpose, fact_keys, grant_id, "
                    "packet_id, reason, prev_hash, row_hash")

    @staticmethod
    def _entry(row) -> LedgerEntry:
        return LedgerEntry(seq=int(row[0]), tenant_ref=str(row[1]), occurred_at=row[2], event=row[3],
                           requester=row[4], source_agent=row[5], purpose=row[6], fact_keys=tuple(row[7]),
                           grant_id=row[8], packet_id=row[9], reason=row[10], prev_hash=row[11], row_hash=row[12])

    def append(self, *, tenant_ref: str, occurred_at: datetime, event: str, requester: str, source_agent: str,
               purpose: str, fact_keys: Iterable[str], grant_id: str = "", packet_id: str = "",
               reason: str = ALLOW_REASON) -> LedgerEntry:
        keys = validate_fields(event, requester, source_agent, purpose, fact_keys, grant_id, packet_id, reason)

        def go(tenant):
            row = self.conn.execute(
                "INSERT INTO public.vault_pull_ledger (tenant_id, seq, occurred_at, event, requester, source_agent,"
                " purpose, fact_keys, grant_id, packet_id, reason, prev_hash, row_hash)"
                " VALUES (%s, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, repeat('0', 64), repeat('0', 64))"
                f" RETURNING {self._LEDGER_COLS}",
                (tenant, occurred_at, event, requester, source_agent, purpose, list(keys), grant_id, packet_id,
                 reason)).fetchone()
            return self._entry(row)
        return self._run(tenant_ref, go)

    def entries(self, tenant_ref: str) -> List[LedgerEntry]:
        def go(tenant):
            rows = self.conn.execute(f"SELECT {self._LEDGER_COLS} FROM public.vault_pull_ledger ORDER BY seq").fetchall()
            return [self._entry(r) for r in rows]
        return self._run(tenant_ref, go)

    def verify(self, tenant_ref: str):
        return verify_chain(self.entries(tenant_ref))

    # ── saved benefits ─────────────────────────────────────────────────────
    def save(self, tenant_ref: str, benefit_id: str, status: str, content_hash: str) -> dict:
        if status not in SAVED_STATUSES:
            raise StoreError(f"status must be one of {', '.join(SAVED_STATUSES)}")

        def go(tenant):
            row = self.conn.execute(
                "INSERT INTO public.vault_saved_benefit (tenant_id, benefit_id, status, content_hash_at_save)"
                " VALUES (%s, %s, %s, %s) ON CONFLICT (tenant_id, benefit_id) DO UPDATE SET status = EXCLUDED.status"
                " RETURNING saved_id, benefit_id, status, content_hash_at_save, saved_at, updated_at",
                (tenant, benefit_id, status, content_hash)).fetchone()
            return self._saved(row)
        return self._run(tenant_ref, go)

    @staticmethod
    def _saved(row) -> dict:
        return {"saved_id": str(row[0]), "benefit_id": row[1], "status": row[2], "content_hash_at_save": row[3],
                "saved_at": row[4].isoformat(), "updated_at": row[5].isoformat()}

    def saved(self, tenant_ref: str) -> List[dict]:
        def go(tenant):
            rows = self.conn.execute(
                "SELECT saved_id, benefit_id, status, content_hash_at_save, saved_at, updated_at"
                " FROM public.vault_saved_benefit ORDER BY saved_at, saved_id").fetchall()
            return [self._saved(r) for r in rows]
        return self._run(tenant_ref, go)

    def discard(self, tenant_ref: str, kind: str, item_id: str) -> bool:
        """Remove a saved benefit, or a revoked or expired grant. False when nothing matched."""
        if kind not in DISCARD_KINDS:
            raise StoreError(f"kind is one of {', '.join(DISCARD_KINDS)}")
        item = _uuid(item_id)

        def go(tenant):
            if item is None:
                return False
            return bool(self.conn.execute("SELECT public.vb_vault_discard(%s, %s::uuid)", (kind, item)).fetchone()[0])
        return self._run(tenant_ref, go)


def load_reviews(conn) -> List[Review]:
    """Named-reviewer VERIFIED marks kept in the database (gate G1)."""
    rows = conn.execute(
        "SELECT benefit_id, verified_by, verified_on, verified_content_hash FROM ref.vault_benefit"
        " WHERE record_status = 'VERIFIED' ORDER BY benefit_id").fetchall()
    return [Review(r[0], r[1], r[2].isoformat(), r[3]) for r in rows]
