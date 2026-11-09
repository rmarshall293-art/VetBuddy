"""Pull grants: the person's permission for one pull scope.

A grant names one source agent, the exact fact keys, one purpose
(``benefit_matching``), the privacy mode, and an expiry. It can be revoked at
any time and stops working at once. A grant can never name a fact the source
does not expose, a fact above the mode's ceiling, or a V3/V4/V5 fact.

Account grants (Mode B) live in ``public.vault_pull_grant`` (vault_store);
session grants (Mode A, at most V1, at most a day) live in memory with the
session.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Dict, FrozenSet, Iterable, List, Optional

from .. import VAULT_AGENT_ID
from ..facts import CATALOG, within_ceiling
from ..vocab import NEVER_PULLABLE, PULL_PURPOSES
from .manifests import ManifestSet


class GrantError(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class PullGrant:
    grant_id: str
    tenant_ref: str
    grantee: str
    source_agent: str
    fact_keys: FrozenSet[str]
    purpose: str
    mode: str
    scope: str                      # "account" (Mode B) or "session" (Mode A)
    granted_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None

    def active(self, now: datetime) -> bool:
        return self.revoked_at is None and self.granted_at <= now < self.expires_at

    def state(self, now: datetime) -> str:
        if self.revoked_at is not None:
            return "REVOKED"
        if now >= self.expires_at:
            return "EXPIRED"
        return "ACTIVE"

    def view(self, now: datetime) -> dict:
        return {
            "grant_id": self.grant_id, "source_agent": self.source_agent, "fact_keys": sorted(self.fact_keys),
            "purpose": self.purpose, "mode": self.mode, "scope": self.scope,
            "granted_at": self.granted_at.isoformat(), "expires_at": self.expires_at.isoformat(),
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None, "state": self.state(now),
        }


def consent_text(manifests: ManifestSet, source_agent: str, fact_keys: Iterable[str], days_or_hours: str) -> str:
    """The sentence shown to the person before they confirm a grant."""
    manifest = manifests.get(source_agent)
    name = manifest.name if manifest else source_agent
    keys = ", ".join(sorted(fact_keys))
    return (f"Let the Benefit Vault read {keys} from {name}, only to look for benefits that may fit you, "
            f"for {days_or_hours}. You can turn this off at any time.")


def new_grant(manifests: ManifestSet, governance: dict, *, tenant_ref: str, source_agent: str,
              fact_keys: Iterable[str], purpose: str, mode: str, now: datetime,
              days: Optional[int] = None, hours: Optional[int] = None) -> PullGrant:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if mode not in ("A", "B"):
        raise GrantError("MODE_C_UNREACHABLE", "grants exist only in Mode A (session) and Mode B (account)")
    if purpose not in PULL_PURPOSES:
        raise GrantError("PURPOSE_NOT_ALLOWED", f"purpose {purpose!r} is not allowed")
    keys = frozenset(fact_keys)
    if not keys:
        raise GrantError("KEY_NOT_GRANTED", "a grant names at least one fact")
    manifest = manifests.get(source_agent)
    if manifest is None:
        raise GrantError("NO_MANIFEST", f"no manifest for {source_agent}")
    if manifest.agent_id == VAULT_AGENT_ID:
        raise GrantError("NOT_EXPOSED", "the vault does not grant access to itself")
    for key in sorted(keys):
        exposure = manifest.exposure(key)
        if exposure is None:
            raise GrantError("NOT_EXPOSED", f"{source_agent} does not expose {key}")
        spec = CATALOG[key]
        if spec.data_class in NEVER_PULLABLE or not spec.pullable:
            raise GrantError("CLASS_NEVER_PULLABLE", f"{key} may never be pulled")
        if not within_ceiling(spec.data_class, mode):
            raise GrantError("CLASS_ABOVE_MODE_CEILING", f"{key} ({spec.data_class}) is above the Mode {mode} ceiling")
    limits = governance["grants"]
    if mode == "A":
        span_hours = hours if hours is not None else limits["session_max_hours"]
        if days is not None or not 1 <= span_hours <= limits["session_max_hours"]:
            raise GrantError("DURATION_NOT_ALLOWED", f"a session grant lasts 1-{limits['session_max_hours']} hours")
        span = timedelta(hours=span_hours)
        scope = "session"
    else:
        span_days = days if days is not None else limits["default_days"]
        if hours is not None or not 1 <= span_days <= limits["max_days"]:
            raise GrantError("DURATION_NOT_ALLOWED", f"an account grant lasts 1-{limits['max_days']} days")
        span = timedelta(days=span_days)
        scope = "account"
    return PullGrant(grant_id=str(uuid.uuid4()), tenant_ref=tenant_ref, grantee=VAULT_AGENT_ID,
                     source_agent=source_agent, fact_keys=keys, purpose=purpose, mode=mode, scope=scope,
                     granted_at=now, expires_at=now + span)


class MemoryGrantStore:
    """Session grants (and test doubles for the database store)."""

    def __init__(self):
        self._grants: Dict[str, PullGrant] = {}

    def add(self, grant: PullGrant) -> PullGrant:
        if grant.grant_id in self._grants:
            raise ValueError("duplicate grant id")
        self._grants[grant.grant_id] = grant
        return grant

    def revoke(self, tenant_ref: str, grant_id: str, now: datetime) -> Optional[PullGrant]:
        grant = self._grants.get(grant_id)
        if grant is None or grant.tenant_ref != tenant_ref:
            return None
        if grant.revoked_at is None:
            grant = replace(grant, revoked_at=now)
            self._grants[grant_id] = grant
        return grant

    def for_source(self, tenant_ref: str, source_agent: str, purpose: str) -> List[PullGrant]:
        return sorted((g for g in self._grants.values()
                       if g.tenant_ref == tenant_ref and g.source_agent == source_agent and g.purpose == purpose),
                      key=lambda g: (g.granted_at, g.grant_id))

    def list(self, tenant_ref: str) -> List[PullGrant]:
        return sorted((g for g in self._grants.values() if g.tenant_ref == tenant_ref),
                      key=lambda g: (g.granted_at, g.grant_id))
