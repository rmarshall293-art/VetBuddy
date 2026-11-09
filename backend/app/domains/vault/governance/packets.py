"""Context packets: the only form in which another agent's facts reach the vault.

A packet is sealed by the broker and opened by the vault. Opening checks
seven invariants; any failure refuses the whole packet.

1. ADDRESSED          addressed to this consumer, for this tenant or session
2. PURPOSE_BOUND      the purpose is benefit_matching and equals the grant's
3. EXPIRING           issued no later than now, not expired, life <= the TTL
4. INTEGRITY          the hash over the canonical body matches
5. MINIMUM_NECESSARY  keys are within the grant and within what was requested
6. CLASS_CEILING      every fact is at its catalog class, within the mode
                      ceiling, and never V3, V4 or V5
7. NON_TRANSFERABLE   the packet is not transferable and the grant names this
                      consumer; ``forward`` always refuses
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, FrozenSet, Iterable, Mapping, Tuple

from ..canonical import sha256_hex, utc_iso
from ..facts import CATALOG, within_ceiling
from ..vocab import NEVER_PULLABLE, PULL_PURPOSES
from .grants import PullGrant

INVARIANTS = (
    "ADDRESSED", "PURPOSE_BOUND", "EXPIRING", "INTEGRITY", "MINIMUM_NECESSARY", "CLASS_CEILING", "NON_TRANSFERABLE",
)


class PacketError(PermissionError):
    def __init__(self, invariant: str, message: str):
        super().__init__(f"{invariant}: {message}")
        self.invariant = invariant


def tenant_hash(tenant_ref: str) -> str:
    return sha256_hex(f"vetbuddy.vault.tenant:{tenant_ref}")


@dataclass(frozen=True)
class ContextPacket:
    packet_id: str
    issued_at: datetime
    expires_at: datetime
    purpose: str
    addressed_to: str
    source_agent: str
    grant_id: str
    tenant_hash: str
    mode: str
    facts: Tuple[Tuple[str, Any, str], ...]       # (key, value, data_class), sorted by key
    transferable: bool
    integrity: str

    def body(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "issued_at": utc_iso(self.issued_at),
            "expires_at": utc_iso(self.expires_at),
            "purpose": self.purpose,
            "addressed_to": self.addressed_to,
            "source_agent": self.source_agent,
            "grant_id": self.grant_id,
            "tenant_hash": self.tenant_hash,
            "mode": self.mode,
            "facts": [[key, value, data_class] for key, value, data_class in self.facts],
            "transferable": self.transferable,
        }

    @property
    def keys(self) -> FrozenSet[str]:
        return frozenset(key for key, _, _ in self.facts)


def seal(*, grant: PullGrant, consumer: str, values: Mapping[str, Any], now: datetime, ttl_seconds: int) -> ContextPacket:
    facts = tuple(sorted((key, value, CATALOG[key].data_class) for key, value in values.items()))
    draft = ContextPacket(
        packet_id=str(uuid.uuid4()), issued_at=now, expires_at=now + timedelta(seconds=ttl_seconds),
        purpose=grant.purpose, addressed_to=consumer, source_agent=grant.source_agent, grant_id=grant.grant_id,
        tenant_hash=tenant_hash(grant.tenant_ref), mode=grant.mode, facts=facts, transferable=False, integrity="",
    )
    return ContextPacket(**{**draft.__dict__, "integrity": sha256_hex(draft.body())})


def open_packet(packet: ContextPacket, *, consumer: str, tenant_ref: str, grant: PullGrant,
                requested: Iterable[str], mode: str, now: datetime, ttl_seconds: int) -> Dict[str, Any]:
    """Check all seven invariants and return the facts, or raise PacketError."""
    if packet.addressed_to != consumer or packet.tenant_hash != tenant_hash(tenant_ref):
        raise PacketError("ADDRESSED", "the packet is for another consumer or tenant")
    if packet.purpose not in PULL_PURPOSES or packet.purpose != grant.purpose:
        raise PacketError("PURPOSE_BOUND", "the packet's purpose does not match its grant")
    if not (packet.issued_at <= now < packet.expires_at) or packet.expires_at - packet.issued_at > timedelta(seconds=ttl_seconds):
        raise PacketError("EXPIRING", "the packet is expired, not yet valid, or lives too long")
    if sha256_hex(packet.body()) != packet.integrity:
        raise PacketError("INTEGRITY", "the packet was changed after it was sealed")
    allowed = frozenset(grant.fact_keys) & frozenset(requested)
    if not packet.keys <= allowed or packet.grant_id != grant.grant_id or packet.source_agent != grant.source_agent:
        raise PacketError("MINIMUM_NECESSARY", "the packet carries facts outside the grant or the request")
    for key, _, data_class in packet.facts:
        spec = CATALOG.get(key)
        if (spec is None or data_class != spec.data_class or data_class in NEVER_PULLABLE
                or not within_ceiling(data_class, mode) or packet.mode != mode):
            raise PacketError("CLASS_CEILING", f"{key} is not allowed at Mode {mode}")
    if packet.transferable or grant.grantee != consumer:
        raise PacketError("NON_TRANSFERABLE", "the packet may only be opened by the agent its grant names")
    return {key: value for key, value, _ in packet.facts}


def forward(packet: ContextPacket, to_agent: str) -> None:
    """Packets are never passed on. This exists so callers fail loudly."""
    raise PacketError("NON_TRANSFERABLE", f"packet {packet.packet_id} cannot be forwarded to {to_agent}")
