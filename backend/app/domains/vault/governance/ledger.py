"""The pull ledger: append-only and hash-chained, keys never values.

Every pull, allowed or denied, and every grant created or revoked becomes one
entry. An entry records which fact keys were involved, never their values.

The chain is per tenant (or per session), so deleting an account removes a
whole chain and never breaks anyone else's. Each entry's hash covers the
previous entry's hash and this entry's fields, joined in a fixed order:

    prev_hash|seq|tenant_ref|occurred_at|event|requester|source_agent|purpose|keys|grant_id|packet_id|reason

``occurred_at`` is UTC with microseconds (``canonical.utc_iso``) and ``keys``
is the sorted keys joined with commas. Migration 0014 computes the same text
in its insert trigger, so a database chain verifies with ``verify_chain``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..canonical import GENESIS_HASH, sha256_hex, utc_iso
from ..vocab import ALLOW_REASON, DENIAL_REASONS, VAULT_EVENTS

_TOKEN = re.compile(r"^[a-z0-9_.:-]*$")
_KEY = re.compile(r"^[a-z][a-z_]*$")
REASONS = frozenset(DENIAL_REASONS) | {ALLOW_REASON}


class LedgerError(ValueError):
    pass


@dataclass(frozen=True)
class LedgerEntry:
    seq: int
    tenant_ref: str
    occurred_at: datetime
    event: str
    requester: str
    source_agent: str
    purpose: str
    fact_keys: Tuple[str, ...]
    grant_id: str
    packet_id: str
    reason: str
    prev_hash: str
    row_hash: str

    def view(self) -> dict:
        return {
            "seq": self.seq, "occurred_at": utc_iso(self.occurred_at), "event": self.event,
            "requester": self.requester, "source_agent": self.source_agent, "purpose": self.purpose,
            "fact_keys": list(self.fact_keys), "grant_id": self.grant_id or None, "packet_id": self.packet_id or None,
            "reason": self.reason, "prev_hash": self.prev_hash, "row_hash": self.row_hash,
        }


def entry_text(prev_hash: str, seq: int, tenant_ref: str, occurred_at: datetime, event: str, requester: str,
               source_agent: str, purpose: str, fact_keys: Sequence[str], grant_id: str, packet_id: str,
               reason: str) -> str:
    return "|".join([
        prev_hash, str(seq), tenant_ref, utc_iso(occurred_at), event, requester, source_agent, purpose,
        ",".join(sorted(fact_keys)), grant_id, packet_id, reason,
    ])


def validate_fields(event: str, requester: str, source_agent: str, purpose: str, fact_keys: Iterable[str],
                    grant_id: str, packet_id: str, reason: str) -> Tuple[str, ...]:
    if event not in VAULT_EVENTS:
        raise LedgerError(f"unknown event {event}")
    if reason not in REASONS:
        raise LedgerError(f"unknown reason {reason}")
    if (event == "PULL_ALLOWED") != (reason == ALLOW_REASON) and event in ("PULL_ALLOWED", "PULL_DENIED"):
        raise LedgerError("an allowed pull has reason ALLOWED and a denied pull has a denial reason")
    for value in (requester, source_agent, purpose, grant_id, packet_id):
        if not _TOKEN.match(value or ""):
            raise LedgerError("ledger fields are tokens; values never enter the ledger")
    keys = tuple(sorted(set(fact_keys)))
    for key in keys:
        if not _KEY.match(key):
            raise LedgerError(f"bad fact key {key!r}")
    return keys


def verify_chain(entries: Sequence[LedgerEntry]) -> Tuple[bool, Optional[int]]:
    """Return (True, None) or (False, first bad seq)."""
    prev = GENESIS_HASH
    for expected_seq, entry in enumerate(entries, start=1):
        text = entry_text(entry.prev_hash, entry.seq, entry.tenant_ref, entry.occurred_at, entry.event,
                          entry.requester, entry.source_agent, entry.purpose, entry.fact_keys, entry.grant_id,
                          entry.packet_id, entry.reason)
        if entry.seq != expected_seq or entry.prev_hash != prev or sha256_hex(text) != entry.row_hash:
            return False, entry.seq
        prev = entry.row_hash
    return True, None


class MemoryLedger:
    """Session ledger (Mode A) and the reference implementation for tests."""

    def __init__(self):
        self._chains: Dict[str, List[LedgerEntry]] = {}

    def append(self, *, tenant_ref: str, occurred_at: datetime, event: str, requester: str, source_agent: str,
               purpose: str, fact_keys: Iterable[str], grant_id: str = "", packet_id: str = "",
               reason: str = ALLOW_REASON) -> LedgerEntry:
        keys = validate_fields(event, requester, source_agent, purpose, fact_keys, grant_id, packet_id, reason)
        if not tenant_ref or not _TOKEN.match(tenant_ref):
            raise LedgerError("tenant_ref is a token")
        chain = self._chains.setdefault(tenant_ref, [])
        prev = chain[-1].row_hash if chain else GENESIS_HASH
        seq = len(chain) + 1
        text = entry_text(prev, seq, tenant_ref, occurred_at, event, requester, source_agent, purpose, keys,
                          grant_id, packet_id, reason)
        entry = LedgerEntry(seq, tenant_ref, occurred_at, event, requester, source_agent, purpose, keys,
                            grant_id, packet_id, reason, prev, sha256_hex(text))
        chain.append(entry)
        return entry

    def entries(self, tenant_ref: str) -> List[LedgerEntry]:
        return list(self._chains.get(tenant_ref, ()))

    def verify(self, tenant_ref: str) -> Tuple[bool, Optional[int]]:
        return verify_chain(self._chains.get(tenant_ref, ()))
