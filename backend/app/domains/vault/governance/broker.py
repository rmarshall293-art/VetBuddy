"""The pull broker: Privacy and Consent Guardian (decision and enforcement point).

The Benefit Vault agent is the only agent that may pull facts from other
agents, and it may do so only through this broker. For each request the
broker decides, enforces, and writes the decision to the pull ledger (keys,
never values), allowed or denied:

    mode C unreachable -> requester may pull -> source has a manifest ->
    purpose allowed -> each key exposed -> class never V3/V4/V5 -> class within
    the mode ceiling -> keys are minimum necessary (rules in scope need them)
    -> an active grant covers every key -> the source is reachable

Only then does it ask the source for values, keep just the granted keys, check
each value against the catalog, and seal a context packet addressed to the
vault. The vault opens the packet with ``packets.open_packet``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, FrozenSet, Iterable, Mapping, Optional, Protocol

from .. import VAULT_AGENT_ID
from ..facts import CATALOG, FactError, validate_value, within_ceiling
from ..vocab import ALLOW_REASON, NEVER_PULLABLE, PULL_PURPOSES
from .grants import PullGrant
from .manifests import ManifestSet
from .packets import ContextPacket, seal


class FactProvider(Protocol):
    """Another agent's store, seen only through this interface."""

    def provide(self, tenant_ref: str, keys: FrozenSet[str]) -> Mapping[str, Any]:
        ...


class GrantSource(Protocol):
    def for_source(self, tenant_ref: str, source_agent: str, purpose: str):
        ...


class LedgerSink(Protocol):
    def append(self, **fields):
        ...


@dataclass(frozen=True)
class PullRequest:
    tenant_ref: str
    requester: str
    source_agent: str
    fact_keys: FrozenSet[str]
    purpose: str
    mode: str
    needed: FrozenSet[str]          # fact keys that rules in scope mention


@dataclass
class PullDecision:
    allowed: bool
    reason: str
    packet: Optional[ContextPacket] = None
    grant: Optional[PullGrant] = None
    delivered: FrozenSet[str] = field(default_factory=frozenset)
    ledger_seq: Optional[int] = None


class PullBroker:
    def __init__(self, manifests: ManifestSet, grants: GrantSource, ledger: LedgerSink,
                 providers: Mapping[str, FactProvider], ttl_seconds: int):
        self.manifests = manifests
        self.grants = grants
        self.ledger = ledger
        self.providers = dict(providers)
        self.ttl_seconds = ttl_seconds

    def _record(self, request: PullRequest, now: datetime, reason: str, keys: Iterable[str],
                grant_id: str = "", packet_id: str = "") -> Optional[int]:
        entry = self.ledger.append(
            tenant_ref=request.tenant_ref, occurred_at=now,
            event="PULL_ALLOWED" if reason == ALLOW_REASON else "PULL_DENIED",
            requester=request.requester if self._safe(request.requester) else "unknown",
            source_agent=request.source_agent if self._safe(request.source_agent) else "unknown",
            purpose=request.purpose if self._safe(request.purpose) else "unknown",
            fact_keys=[k for k in keys if k in CATALOG], grant_id=grant_id, packet_id=packet_id, reason=reason,
        )
        return getattr(entry, "seq", None)

    @staticmethod
    def _safe(token: str) -> bool:
        return bool(token) and all(ch.isalnum() or ch in "_.:-" for ch in token) and token.lower() == token

    def _deny(self, request: PullRequest, now: datetime, reason: str, grant: Optional[PullGrant] = None) -> PullDecision:
        seq = self._record(request, now, reason, request.fact_keys, grant.grant_id if grant else "")
        return PullDecision(False, reason, grant=grant, ledger_seq=seq)

    def request(self, request: PullRequest, now: datetime) -> PullDecision:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        if request.mode not in ("A", "B"):
            return self._deny(request, now, "MODE_C_UNREACHABLE")
        requester = self.manifests.get(request.requester)
        if requester is None or not requester.may_pull_from_agents or request.requester != VAULT_AGENT_ID:
            return self._deny(request, now, "REQUESTER_NOT_PERMITTED")
        source = self.manifests.get(request.source_agent)
        if source is None:
            return self._deny(request, now, "NO_MANIFEST")
        if request.purpose not in PULL_PURPOSES:
            return self._deny(request, now, "PURPOSE_NOT_ALLOWED")
        if not request.fact_keys:
            return self._deny(request, now, "NOT_MINIMUM_NECESSARY")
        for key in sorted(request.fact_keys):
            if key not in CATALOG or source.exposure(key) is None:
                return self._deny(request, now, "NOT_EXPOSED")
        for key in sorted(request.fact_keys):
            spec = CATALOG[key]
            if spec.data_class in NEVER_PULLABLE or not spec.pullable:
                return self._deny(request, now, "CLASS_NEVER_PULLABLE")
            if not within_ceiling(spec.data_class, request.mode):
                return self._deny(request, now, "CLASS_ABOVE_MODE_CEILING")
        if not request.fact_keys <= request.needed:
            return self._deny(request, now, "NOT_MINIMUM_NECESSARY")
        grants = self.grants.for_source(request.tenant_ref, request.source_agent, request.purpose)
        live = [g for g in grants if g.active(now) and g.mode == request.mode and g.grantee == VAULT_AGENT_ID]
        covering = [g for g in live if request.fact_keys <= g.fact_keys]
        if not covering:
            if live:
                return self._deny(request, now, "KEY_NOT_GRANTED", live[-1])
            if any(g.revoked_at is not None for g in grants):
                return self._deny(request, now, "GRANT_REVOKED", grants[-1])
            if grants:
                return self._deny(request, now, "GRANT_EXPIRED", grants[-1])
            return self._deny(request, now, "NO_ACTIVE_GRANT")
        grant = covering[-1]
        provider = self.providers.get(request.source_agent)
        if provider is None:
            return self._deny(request, now, "SOURCE_UNAVAILABLE", grant)
        try:
            raw = provider.provide(request.tenant_ref, frozenset(request.fact_keys))
        except Exception:  # the source failing is a denial, never a crash in the vault
            return self._deny(request, now, "SOURCE_UNAVAILABLE", grant)
        values: Dict[str, Any] = {}
        for key in sorted(request.fact_keys & grant.fact_keys):
            if key in raw:
                try:
                    values[key] = validate_value(key, raw[key])
                except FactError:
                    continue
        packet = seal(grant=grant, consumer=VAULT_AGENT_ID, values=values, now=now, ttl_seconds=self.ttl_seconds)
        seq = self._record(request, now, ALLOW_REASON, values.keys(), grant.grant_id, packet.packet_id)
        return PullDecision(True, ALLOW_REASON, packet=packet, grant=grant, delivered=frozenset(values), ledger_seq=seq)
