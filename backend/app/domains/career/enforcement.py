"""Audit, consent, protected content, evidence, fabrication guard and the assembly gate.

Fixes carried from the specification (ADR 0007 maps each to a test):
  D-1  only metrics license numbers; structural digits are removed from the claim
  D-2  protected content is checked first, per statement
  D-10 text quoted from the announcement is not a claim about the person
plus the §16.3 and §16.4 gaps, closed here:
  - the no-provenance exemption lives in the gate, not in a renderer, and only
    for sentences that claim no number
  - sensitive records need a per-document opt-in
  - hiring guarantees are held by the gate (assert_no_hiring_guarantee is wired)
  - rejected consent grants are audited; audit events are immutable, carry a
    full UUID, a total order, a full UTC timestamp and split actor fields
  - adding a duplicate evidence id is refused; verifying an unknown id raises
    EvidenceError; a record of absence can never be made outbound
  - a field that is health, protected-class or financial detail can never be
    granted to the career module, whatever the source (fact-level allowlist, CB-02)
"""
from __future__ import annotations

import datetime as dt
import itertools
import json
import re
import uuid
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Mapping, Optional, Sequence, Tuple

RULES_FILE = Path(__file__).resolve().parents[4] / "config" / "career_rules.json"
RULES: dict = json.loads(RULES_FILE.read_text(encoding="utf-8"))

NEEDS_VERIFICATION: str = RULES["needs_verification"]
AUDIT_ACTIONS: FrozenSet[str] = frozenset(RULES["audit_actions"])


def _rx(pattern: str, flags: str) -> "re.Pattern[str]":
    return re.compile(pattern, re.I if "i" in flags else 0)


# ── audit ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AuditEvent:
    seq: int
    action: str
    record: str
    reason: str
    actor_user: Optional[str] = None
    actor_agent: Optional[str] = None
    previous_value: Any = None
    new_value: Any = None
    approval: Optional[str] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


class AuditLog:
    """Append-only in memory; events are frozen and the action vocabulary is closed.
    Persistence maps onto the platform's hash-chained audit_event (slice 01)."""

    def __init__(self):
        self._events: List[AuditEvent] = []
        self._seq = itertools.count(1)

    def record(self, action: str, record: str, reason: str, **kw) -> AuditEvent:
        if action not in AUDIT_ACTIONS:
            raise ValueError(f"unknown audit action {action!r}")
        event = AuditEvent(seq=next(self._seq), action=action, record=record, reason=reason, **kw)
        self._events.append(event)
        return event

    def __len__(self) -> int:
        return len(self._events)

    @property
    def events(self) -> Tuple[AuditEvent, ...]:
        return tuple(self._events)

    def for_record(self, record: str) -> List[AuditEvent]:
        return [e for e in self._events if e.record == record]


# ── consent ──────────────────────────────────────────────────────────────────

class ConsentError(PermissionError):
    pass


CATALOG: Dict[str, dict] = {m["id"]: m for m in RULES["module_catalog"]}
STRUCTURALLY_SEVERED: FrozenSet[str] = frozenset(m["id"] for m in RULES["module_catalog"] if m.get("severed"))
NEVER_GRANTABLE: FrozenSet[str] = frozenset(RULES["never_grantable_fields"])
DESTINATION = "career_navigator"


@dataclass(frozen=True)
class ConsentGrant:
    user_id: str
    tenant_id: str
    source_module: str
    purpose: str
    allowed_fields: FrozenSet[str]
    granted_on: dt.date
    expires_on: Optional[dt.date] = None
    revoked: bool = False
    destination_module: str = DESTINATION

    def active_on(self, when: dt.date) -> bool:
        if self.revoked or when < self.granted_on:
            return False
        return self.expires_on is None or when <= self.expires_on


class ConsentBroker:
    """The only path by which another module's data reaches career analysis.

    Gated by fact, not by class (CB-02): a grant may name only fields the
    module catalog lists for that source, never a field on the never-grantable
    list, and never anything from a severed module. Severance is checked at
    grant and at read; a refused grant is audited."""

    def __init__(self, audit: AuditLog):
        self._grants: List[ConsentGrant] = []
        self._audit = audit

    def _refuse(self, g: ConsentGrant, why: str):
        self._audit.record("consent.grant.refused", f"{g.source_module}->{g.destination_module}", why,
                           actor_user=g.user_id, actor_agent="consent_broker", new_value=sorted(g.allowed_fields))
        raise ConsentError(why)

    def grant(self, g: ConsentGrant) -> None:
        if g.destination_module != DESTINATION:
            self._refuse(g, "career consent grants name the career navigator as destination")
        if g.source_module in STRUCTURALLY_SEVERED:
            self._refuse(g, f"{g.source_module} is structurally severed from career data; no consent can change that")
        entry = CATALOG.get(g.source_module)
        if entry is None:
            self._refuse(g, f"unknown source module {g.source_module}")
        if g.purpose != entry["purpose"]:
            self._refuse(g, f"{g.source_module} may be read only for {entry['purpose']}")
        forbidden = sorted(g.allowed_fields & NEVER_GRANTABLE)
        if forbidden:
            self._refuse(g, f"never grantable to career: {', '.join(forbidden)}")
        unlisted = sorted(g.allowed_fields - frozenset(entry["fields"]))
        if unlisted:
            self._refuse(g, f"not on the {g.source_module} allowlist: {', '.join(unlisted)}")
        if not g.allowed_fields:
            self._refuse(g, "a grant names at least one field")
        self._grants.append(g)
        self._audit.record("consent.granted", f"{g.source_module}->{g.destination_module}", g.purpose,
                           actor_user=g.user_id, actor_agent="consent_broker", new_value=sorted(g.allowed_fields))

    def revoke(self, user_id: str, source: str) -> int:
        """Broad on purpose: revoking a source ends every purpose and tenant for that user."""
        n = 0
        for i, g in enumerate(self._grants):
            if g.user_id == user_id and g.source_module == source and not g.revoked:
                self._grants[i] = replace(g, revoked=True)
                n += 1
        if n:
            self._audit.record("consent.revoked", f"{source}->{DESTINATION}", f"{n} grant(s) revoked",
                               actor_user=user_id, actor_agent="consent_broker")
        return n

    def read(self, *, user_id: str, tenant_id: str, source: str, purpose: str, requested_fields: Iterable[str],
             payload: Mapping[str, Any], requesting_agent: str, when: Optional[dt.date] = None) -> Dict[str, Any]:
        when = when or dt.date.today()
        requested = set(requested_fields)
        record = f"{source}->{DESTINATION}"
        if source in STRUCTURALLY_SEVERED:
            self._audit.record("crossmodule.read.denied", record, "structurally severed module",
                               actor_agent=requesting_agent, actor_user=user_id)
            raise ConsentError(f"{source} is structurally severed from career data")
        grant = next((g for g in self._grants if g.user_id == user_id and g.tenant_id == tenant_id
                      and g.source_module == source and g.purpose == purpose and g.active_on(when)), None)
        if grant is None:
            self._audit.record("crossmodule.read.denied", record, f"no active grant for {purpose}",
                               actor_agent=requesting_agent, actor_user=user_id)
            raise ConsentError(f"no active grant from {source} for {purpose}")
        authorized = (requested & grant.allowed_fields) - NEVER_GRANTABLE      # belt and braces
        result = {k: v for k, v in payload.items() if k in authorized}
        self._audit.record("crossmodule.read", record, purpose, actor_agent=requesting_agent, actor_user=user_id,
                           new_value={"returned": sorted(result), "denied": sorted(requested - authorized)})
        return result


# ── protected content ────────────────────────────────────────────────────────

PROTECTED_PATTERNS: Tuple[Tuple[str, "re.Pattern[str]"], ...] = tuple(
    (name, _rx(p, flags)) for name, p, flags in RULES["protected_patterns"])


@dataclass(frozen=True)
class ProtectedFinding:
    field_name: str
    excerpt: str


class ProtectedFieldGuard:
    """Detects; the assembler holds. Employer-facing artifacts are held, not
    sanitized: silent redaction hides what the system almost disclosed."""

    def scan(self, text: str) -> List[ProtectedFinding]:
        found, seen = [], set()
        for name, pat in PROTECTED_PATTERNS:
            m = pat.search(text)
            if m and name not in seen:
                seen.add(name)
                found.append(ProtectedFinding(name, m.group(0).strip()))
        return found


CLAUSE = re.compile(r"(?<=[.;!?,])\s+|\n+")   # a protected fact is dropped with its clause


def redact_protected(text: str) -> str:
    """Remove protected spans before any matching, so health and protected-class
    content can neither help nor hurt a match (ADA invariance, CB-01).

    The whole clause goes, not just the matched span: "Manages PTSD with weekly
    therapy" minus its diagnosis still leaves "manages" to match on, and a rating
    pattern can leave "disabled" behind. A clause that carries a protected fact
    contributes nothing to matching."""
    kept = [s for s in CLAUSE.split(text) if not any(pat.search(s) for _, pat in PROTECTED_PATTERNS)]
    return " ".join(kept)


# ── evidence ─────────────────────────────────────────────────────────────────

class Verification(str, Enum):
    UNVERIFIED = "unverified"
    USER_ATTESTED = "user_attested"
    DOCUMENT_BACKED = "document_backed"


OUTBOUND_OK = frozenset({Verification.USER_ATTESTED, Verification.DOCUMENT_BACKED})
KINDS = ("military_experience", "civilian_experience", "education", "credential", "accomplishment")


class EvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class Metric:
    value_text: str                      # the literal string a document may use ("$4.2 million", "31")
    meaning: str                         # what it counts
    source: str                          # where the figure comes from
    verification: Verification = Verification.UNVERIFIED
    phrase: Optional[str] = None         # sentence template with {v}, reviewed with the figure (D8)


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    kind: str
    title: str
    summary: str
    verification: Verification = Verification.UNVERIFIED
    metrics: Tuple[Metric, ...] = ()
    org: Optional[str] = None
    start_date: Optional[str] = None     # "YYYY-MM"
    end_date: Optional[str] = None       # None = present
    hours_per_week: Optional[int] = None
    skills: Tuple[str, ...] = ()
    source_ref: Optional[str] = None
    sensitive: bool = False              # disclosure needs a per-document opt-in
    negative: bool = False               # documents an ABSENCE; never support, never outbound (D-4)

    def __post_init__(self):
        if self.kind not in KINDS:
            raise EvidenceError(f"kind must be one of {', '.join(KINDS)}")
        if self.negative and self.verification in OUTBOUND_OK:
            raise EvidenceError("a record of absence can never be outbound evidence")

    @property
    def outbound(self) -> bool:
        return self.verification in OUTBOUND_OK and not self.negative

    def verified_numbers(self) -> set:
        """Metrics only (D-1). Structural fields such as hours_per_week never license
        a number: 'Cut costs by 40%' must not pass because the record says 40 hours."""
        if not self.outbound:
            return set()
        return {n for m in self.metrics if m.verification in OUTBOUND_OK for n in numbers_in(m.value_text)}


class EvidenceBank:
    def __init__(self, audit: AuditLog, items: Iterable[EvidenceItem] = ()):
        self._items: Dict[str, EvidenceItem] = {}
        self._audit = audit
        for item in items:
            self.add(item)

    def add(self, item: EvidenceItem) -> EvidenceItem:
        if item.evidence_id in self._items:
            raise EvidenceError(f"evidence {item.evidence_id} already exists; records are never silently replaced")
        self._items[item.evidence_id] = item
        return item

    def get(self, evidence_id: str) -> Optional[EvidenceItem]:
        return self._items.get(evidence_id)

    def all(self) -> List[EvidenceItem]:
        return list(self._items.values())

    def __len__(self) -> int:
        return len(self._items)

    def verify(self, evidence_id: str, level: Verification, actor: str) -> EvidenceItem:
        """Attest or document a record (or correct it downward); always audited."""
        item = self._items.get(evidence_id)
        if item is None:
            raise EvidenceError(f"no evidence {evidence_id}")
        if item.negative and level in OUTBOUND_OK:
            raise EvidenceError("a record of absence can't be attested as support; add the credential itself instead")
        # The record only: each figure keeps its own verification, so attesting a
        # record never licenses a number nobody confirmed (spec §9.4).
        updated = replace(item, verification=level)
        self._items[evidence_id] = updated
        self._audit.record("evidence.verified", evidence_id, "user verification", actor_user=actor,
                           previous_value=item.verification.value, new_value=level.value, approval=actor)
        return updated


# ── fabrication guard ────────────────────────────────────────────────────────

_NUMBER = re.compile(RULES["number_token"])
STRUCTURAL: Tuple["re.Pattern[str]", ...] = tuple(_rx(p, f) for p, f in RULES["structural_patterns"])
PROHIBITED_ASSURANCES = re.compile(RULES["prohibited_assurances"], re.I)


def numbers_in(text: str) -> set:
    return {m.group(0).replace(",", "") for m in _NUMBER.finditer(text)}


def strip_structural(text: str) -> str:
    for pat in STRUCTURAL:
        text = pat.sub(" ", text)
    return text


def assert_no_hiring_guarantee(text: str) -> None:
    m = PROHIBITED_ASSURANCES.search(text)
    if m:
        raise ValueError(f"prohibited assurance: {m.group(0)!r}")


@dataclass(frozen=True)
class Statement:
    text: str
    evidence_ids: Tuple[str, ...]
    section: str = "experience"
    quoted: Optional[str] = None             # announcement text echoed, excised before the numeric check (D-10)
    no_provenance_ok: bool = False           # a sentence with no factual claim (an opening line); numbers still refused


@dataclass(frozen=True)
class Finding:
    statement: str
    problem: str
    detail: str


PROBLEMS = ("no_provenance", "unknown_evidence", "unverified_evidence", "absence_record", "untraceable_metric",
            "protected_content", "sensitive_not_opted_in", "prohibited_assurance")


class FabricationGuard:
    def __init__(self, bank: EvidenceBank):
        self._bank = bank

    def check(self, stmt: Statement, *, sensitive_opt_in: FrozenSet[str] = frozenset()) -> List[Finding]:
        findings: List[Finding] = []
        m = PROHIBITED_ASSURANCES.search(stmt.text)
        if m:
            findings.append(Finding(stmt.text, "prohibited_assurance",
                                    f"Says {m.group(0)!r}. No document may promise a hiring outcome."))
        claim = stmt.text
        if stmt.quoted:
            claim = re.sub(re.escape(stmt.quoted), " ", claim, flags=re.I)
        claimed = numbers_in(strip_structural(claim))
        if not stmt.evidence_ids:
            if stmt.no_provenance_ok and not claimed:
                return findings
            return findings + [Finding(stmt.text, "no_provenance", NEEDS_VERIFICATION)]
        cited: List[EvidenceItem] = []
        for eid in stmt.evidence_ids:
            item = self._bank.get(eid)
            if item is None:
                findings.append(Finding(stmt.text, "unknown_evidence", f"Cites {eid}, which is not in the evidence bank."))
            elif item.negative:
                findings.append(Finding(stmt.text, "absence_record",
                                        f"{item.title} documents that something is NOT on file; it can't support a claim."))
            elif not item.outbound:
                findings.append(Finding(stmt.text, "unverified_evidence", NEEDS_VERIFICATION))
            elif item.sensitive and eid not in sensitive_opt_in:
                findings.append(Finding(stmt.text, "sensitive_not_opted_in",
                                        f"{item.title} is marked sensitive; include it only if you choose to for this document."))
            else:
                cited.append(item)
        if not cited:                         # don't report numbers when the evidence itself is the problem
            return findings
        allowed = set().union(*(i.verified_numbers() for i in cited))
        for n in sorted(claimed - allowed):
            findings.append(Finding(stmt.text, "untraceable_metric",
                                    f"The figure {n} isn't recorded on the cited evidence. {NEEDS_VERIFICATION}"))
        return findings


# ── assembly gate ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Held:
    statement: Statement
    findings: Tuple[Finding, ...]          # empty = collateral: fine on its own, but its document was voided


@dataclass(frozen=True)
class AssemblyResult:
    document_id: str
    accepted: Tuple[Statement, ...]
    held: Tuple[Held, ...]
    protected_findings: Tuple[ProtectedFinding, ...]
    voided: bool

    @property
    def clean(self) -> bool:
        return not self.held and not self.protected_findings


class DocumentAssembler:
    """Protected content first, per statement (D-2); any protected hit voids the
    whole document, and lines that were fine come back held with no findings."""

    def __init__(self, bank: EvidenceBank, audit: AuditLog):
        self._fab = FabricationGuard(bank)
        self._protected = ProtectedFieldGuard()
        self._audit = audit

    def assemble(self, statements: Sequence[Statement], *, document_id: str, actor: str,
                 sensitive_opt_in: FrozenSet[str] = frozenset()) -> AssemblyResult:
        accepted: List[Statement] = []
        held: List[Held] = []
        protected: List[ProtectedFinding] = []
        for s in statements:
            hits = self._protected.scan(s.text)
            if hits:
                protected.extend(hits)
                held.append(Held(s, tuple(Finding(s.text, "protected_content",
                                                  f"Contains {h.field_name} ({h.excerpt!r}), which may not appear on "
                                                  "an employer-facing document.") for h in hits)))
                continue
            findings = self._fab.check(s, sensitive_opt_in=sensitive_opt_in)
            if findings:
                held.append(Held(s, tuple(findings)))
            else:
                accepted.append(s)
        if protected:
            names = ", ".join(sorted({p.field_name for p in protected}))
            self._audit.record("document.held.protected_content", document_id, names, actor_user=actor,
                               actor_agent="assembly_gate")
            return AssemblyResult(document_id, (), tuple(held) + tuple(Held(s, ()) for s in accepted),
                                  tuple(protected), True)
        self._audit.record("document.assembled", document_id, f"{len(accepted)} accepted, {len(held)} held",
                           actor_user=actor, actor_agent="assembly_gate")
        return AssemblyResult(document_id, tuple(accepted), tuple(held), (), False)
