"""The Benefit Vault agent (plane 5).

The agent searches and matches benefits and deals for service members,
veterans and their families, and explains what the encoded rules say. It
orchestrates, gathers and explains; it never decides. It is the only agent
allowed to pull facts from other agents, and it does that only through the
pull broker, with the person's grant, for the facts the rules in scope need.

Pipeline for every request:

    CrisisGate -> MSTNarrativeGuard -> PIIMinimizer -> facts (mode ceiling)
    -> pulls through the broker (grants, packets, ledger) -> matcher or search
    -> CitationValidator -> ClaimsBoundaryGuard -> (no model call)
    -> OutputGuard (envelope) ; writes pass the ApprovalGate first.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence

from . import VAULT_AGENT_ID
from .envelope import build as build_envelope, facts_canonical
from .facts import CATALOG, Fact, FactError, FactSet, facts_for_tokens, within_ceiling
from .governance.broker import FactProvider, PullBroker, PullRequest
from .governance.egress import EgressGuard
from .governance.grants import GrantError, MemoryGrantStore, consent_text, new_grant
from .governance.ledger import MemoryLedger
from .governance.manifests import ManifestSet
from .governance.packets import PacketError, open_packet
from .guards import (ApprovalGate, ClaimsBoundaryGuard, CrisisGate, LanguageGuard, MSTNarrativeGuard,
                     OutputBlocked, PIIMinimizer)
from .household import member_facts, parse_members
from .matcher import MatchOptions, Matcher
from .registry import VaultRegistry
from .rules import tokens
from .search import Search, SearchQuery
from .vocab import CATEGORIES, GROUPS, KINDS, SAVED_STATUSES


class RequestError(ValueError):
    """The request is malformed; the API answers 422."""


class ModeError(PermissionError):
    """The request needs a mode this session does not have."""


@dataclass
class Session:
    """One caller's context. Mode A is a guest session; Mode B a private account."""

    mode: str
    tenant_ref: str
    grants: Any = field(default_factory=MemoryGrantStore)
    ledger: Any = field(default_factory=MemoryLedger)
    saved: Any = None                  # VaultStore in Mode B

    def __post_init__(self):
        if self.mode not in ("A", "B"):
            raise ModeError("Mode C is unreachable in this build")


def _set(value, allowed, name) -> Optional[FrozenSet[str]]:
    if value in (None, [], ()):
        return None
    if not isinstance(value, (list, tuple)) or not all(isinstance(v, str) for v in value):
        raise RequestError(f"{name} is a list of strings")
    bad = sorted(set(value) - set(allowed))
    if bad:
        raise RequestError(f"unknown {name}: {', '.join(bad)}")
    return frozenset(value)


def _as_of(value, now: datetime) -> date:
    if value is None:
        return now.date()
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise RequestError("as_of is a date such as 2026-10-27") from None


class BenefitVaultAgent:
    agent_id = VAULT_AGENT_ID

    def __init__(self, registry: VaultRegistry, *, providers: Optional[Mapping[str, FactProvider]] = None,
                 environment: Optional[str] = None):
        self.registry = registry
        self.environment = environment
        self.matcher = Matcher(registry)
        self.searcher = Search(registry)
        self.manifests = ManifestSet.from_registry(registry)
        self.egress = EgressGuard.from_registry(registry)
        self.language = LanguageGuard()
        self.crisis = CrisisGate()
        self.mst = MSTNarrativeGuard(self.crisis)
        self.pii = PIIMinimizer()
        self.claims = ClaimsBoundaryGuard()
        self.approval = ApprovalGate()
        self.providers = dict(providers or {})
        self.ttl = int(registry.governance["packets"]["ttl_seconds"])

    # ── shared steps ───────────────────────────────────────────────────────
    def _envelope(self, kind: str, session: Session, policy, inputs, payload) -> dict:
        return build_envelope(self.registry, kind=kind, mode=session.mode, policy=policy, inputs=inputs,
                              payload=payload, language=self.language)

    def _screen(self, text: Optional[str], session: Session) -> Optional[dict]:
        """CrisisGate then MSTNarrativeGuard; a hit ends the request."""
        if self.crisis.triggered(text):
            return self._envelope("crisis_floor", session, None, {"screened": True}, self.crisis.response())
        if self.mst.triggered(text):
            return self._envelope("support_resources", session, None, {"screened": True}, self.mst.response())
        return None

    def _facts(self, request: Mapping) -> FactSet:
        raw = request.get("facts") or {}
        if not isinstance(raw, Mapping):
            raise RequestError("facts is an object")
        unsure = request.get("unsure") or []
        if not isinstance(unsure, list) or not set(unsure) <= set(raw):
            raise RequestError("unsure lists keys that appear in facts")
        values = dict(raw)
        values.setdefault("relationship", "self")
        try:
            return FactSet.from_mapping(values, uncertain=frozenset(unsure))
        except FactError as exc:
            raise RequestError(str(exc)) from None

    def _options(self, request: Mapping, session: Session, now: datetime) -> MatchOptions:
        jurisdictions = request.get("jurisdictions")
        if jurisdictions is not None and (not isinstance(jurisdictions, list) or not jurisdictions):
            raise RequestError("jurisdictions is a non-empty list")
        return MatchOptions(
            as_of=_as_of(request.get("as_of"), now), environment=self.environment, mode=session.mode,
            jurisdictions=tuple(jurisdictions) if jurisdictions else None,
            categories=_set(request.get("categories"), CATEGORIES, "categories"),
            kinds=_set(request.get("kinds"), KINDS, "kinds"),
            include_non_matches=bool(request.get("include_non_matches", False)),
        )

    def needed_keys(self, facts: FactSet, options: MatchOptions, mode: str) -> FrozenSet[str]:
        """Facts that rules in scope mention, that are unknown, and that this mode may hold."""
        scope = self.matcher.scope(facts, options.jurisdictions)
        keys = set()
        for benefit in self.matcher.candidates(scope, options):
            keys |= facts_for_tokens(tokens(benefit.node))
        return frozenset(k for k in keys - set(facts.keys())
                         if within_ceiling(CATALOG[k].data_class, mode) and CATALOG[k].pullable)

    def _pull(self, facts: FactSet, options: MatchOptions, session: Session, now: datetime) -> List[dict]:
        """Ask the broker for needed facts under each active grant the person has given.

        One request per grant, so a person who granted keys from one source in
        two separate grants gets both; no key is asked of the same source twice.
        """
        decisions = []
        needed = self.needed_keys(facts, options, session.mode)
        if not needed:
            return decisions
        broker = PullBroker(self.manifests, session.grants, session.ledger, self.providers, self.ttl)
        granted_sources = sorted({g.source_agent for g in session.grants.list(session.tenant_ref)
                                  if g.active(now) and g.mode == session.mode})
        for source_agent in granted_sources:
            manifest = self.manifests.get(source_agent)
            if manifest is None:
                continue
            live = [g for g in session.grants.for_source(session.tenant_ref, source_agent, "benefit_matching")
                    if g.active(now) and g.mode == session.mode]
            asked: FrozenSet[str] = frozenset()
            for grant in live:
                ask = frozenset((needed & manifest.exposed_keys & grant.fact_keys) - asked)
                if not ask:
                    continue
                asked |= ask
                request = PullRequest(tenant_ref=session.tenant_ref, requester=VAULT_AGENT_ID,
                                      source_agent=source_agent, fact_keys=ask, purpose="benefit_matching",
                                      mode=session.mode, needed=needed)
                decision = broker.request(request, now)
                entry = {"source_agent": source_agent, "allowed": decision.allowed, "reason": decision.reason,
                         "fact_keys": sorted(ask), "delivered": sorted(decision.delivered)}
                if decision.allowed and decision.packet is not None:
                    try:
                        values = open_packet(decision.packet, consumer=VAULT_AGENT_ID, tenant_ref=session.tenant_ref,
                                             grant=decision.grant, requested=ask, mode=session.mode, now=now,
                                             ttl_seconds=self.ttl)
                    except PacketError as exc:
                        entry.update(allowed=False, reason=f"PACKET_{exc.invariant}", delivered=[])
                        values = {}
                    for key, value in sorted(values.items()):
                        if not facts.has(key):
                            facts.put(Fact(key, value, "pulled", True, source_agent))
                    needed = needed - frozenset(values)
                decisions.append(entry)
        return decisions

    @staticmethod
    def _questions(items: Sequence[dict], limit: int = 8) -> List[dict]:
        counts: Dict[str, dict] = {}
        for item in items:
            for need in item["facts_needed"]:
                entry = counts.setdefault(need["fact_key"], {**need, "records": 0})
                entry["records"] += 1
        ranked = sorted(counts.values(), key=lambda q: (-q["records"], q["fact_key"]))
        return ranked[:limit]

    # ── match ──────────────────────────────────────────────────────────────
    def match(self, request: Mapping, session: Session, now: datetime) -> dict:
        screened = self._screen(request.get("note"), session)
        if screened:
            return screened
        facts = self._facts(request)
        options = self._options(request, session, now)
        facts, dropped = facts.limited_to(session.mode)
        pulls = self._pull(facts, options, session, now) if request.get("pull", True) else []
        result = self.matcher.match(facts, options)
        problems = self.claims.check(result.items)
        if problems:
            raise OutputBlocked(problems)
        general = [{"id": "mode_a_dropped", "text": self.registry.caveats["mode_a_dropped"]}] if dropped else []
        payload = {
            "subject": {
                "relationship": facts.get("relationship"),
                "facts_used": sorted(facts.keys()),
                "facts_not_used_in_this_mode": sorted(dropped),
                "facts_pulled": sorted(({"fact_key": k, "source_agent": f.source_agent}
                                        for k, f in facts.facts.items() if f.provenance == "pulled"),
                                       key=lambda x: x["fact_key"]),
                "pulls": pulls,
            },
            "scope": list(result.scope),
            "evaluated": result.evaluated,
            "counts": result.counts,
            "questions": self._questions(result.items),
            "general_caveats": general,
            "items": result.items,
        }
        inputs = {"facts": facts_canonical(facts), "options": options.canonical(), "dropped": sorted(dropped)}
        return self._envelope("match", session, result.policy, inputs, payload)

    # ── household ──────────────────────────────────────────────────────────
    def household(self, request: Mapping, session: Session, now: datetime) -> dict:
        screened = self._screen(request.get("note"), session)
        if screened:
            return screened
        sponsor = self._facts(request)
        if sponsor.get("relationship") != "self":
            raise RequestError("household facts describe the service member or veteran (relationship self)")
        options = self._options(request, session, now)
        try:
            members = parse_members(request.get("members"))
        except FactError as exc:
            raise RequestError(str(exc)) from None
        if not members:
            raise RequestError("members lists at least one spouse or child")
        sponsor, dropped = sponsor.limited_to(session.mode)
        out = []
        inputs_members = []
        policy = self.registry.publish_policy(self.environment)
        for member in members:
            try:
                facts, member_dropped = member_facts(sponsor, member).limited_to(session.mode)
            except FactError as exc:
                raise RequestError(str(exc)) from None
            result = self.matcher.match(facts, options)
            problems = self.claims.check(result.items)
            if problems:
                raise OutputBlocked(problems)
            out.append({"member_id": member.member_id, "relationship": member.relationship,
                        "facts_used": sorted(facts.keys()), "facts_not_used_in_this_mode": sorted(member_dropped),
                        "scope": list(result.scope), "evaluated": result.evaluated, "counts": result.counts,
                        "questions": self._questions(result.items), "items": result.items})
            inputs_members.append({"member_id": member.member_id, "facts": facts_canonical(facts)})
        payload = {"sponsor": {"facts_used": sorted(sponsor.keys()), "facts_not_used_in_this_mode": sorted(dropped)},
                   "members": out}
        inputs = {"sponsor": facts_canonical(sponsor), "members": inputs_members, "options": options.canonical()}
        return self._envelope("household", session, policy, inputs, payload)

    # ── search and read ────────────────────────────────────────────────────
    def listing(self, benefit) -> dict:
        source = self.registry.sources[benefit.source_id]
        caveats = list(benefit.caveat_ids)
        if benefit.kind == "COMMERCIAL_DEAL":
            caveats.append("commercial")
        elif benefit.kind == "NONPROFIT_PROGRAM":
            caveats.append("nonprofit")
        if benefit.official_url_status == "SEEN_IN_SEARCH":
            caveats.append("seen_in_search")
        if benefit.record_status != "VERIFIED":
            caveats.append("not_verified")
        if source["tail_unread_chars"]:
            caveats.append("tail_unread")
        return {
            "benefit_id": benefit.benefit_id, "title": benefit.title, "jurisdiction": benefit.jurisdiction,
            "category": benefit.category, "kind": benefit.kind, "groups": list(benefit.groups),
            "who_it_is_for": benefit.who_it_is_for, "value": benefit.value,
            "official_url": benefit.official_url if self.egress.allowed(benefit.official_url) else None,
            "record_status": benefit.record_status, "verified_by": benefit.verified_by,
            "source": {"tier": benefit.source_tier, "page_status": source["page_status"],
                       "url_status": benefit.official_url_status, "opened_on": source["opened_on"],
                       "page_updated": source["page_updated"]},
            "caveats": [{"id": c, "text": self.registry.caveats[c]} for c in dict.fromkeys(caveats)],
        }

    def search(self, request: Mapping, session: Session) -> dict:
        text = request.get("q") or ""
        if not isinstance(text, str):
            raise RequestError("q is text")
        screened = self._screen(text, session)
        if screened:
            return screened
        cleaned, removed = self.pii.minimize(text)
        jurisdictions = request.get("jurisdictions")
        try:
            query = SearchQuery(
                text=cleaned,
                jurisdictions=tuple(jurisdictions) if jurisdictions else None,
                categories=_set(request.get("categories"), CATEGORIES, "categories"),
                groups=_set(request.get("groups"), GROUPS, "groups"),
                kinds=_set(request.get("kinds"), KINDS, "kinds"),
                limit=int(request.get("limit", 25)), offset=int(request.get("offset", 0)),
            )
            page, total = self.searcher.run(query)
        except (TypeError, ValueError) as exc:
            raise RequestError(str(exc)) from None
        payload = {"query": cleaned, "identifiers_removed": removed, "total": total, "offset": query.offset,
                   "items": [self.listing(b) for b in page]}
        inputs = {"q": cleaned, "jurisdictions": list(query.jurisdictions or ()), "limit": query.limit,
                  "offset": query.offset, "categories": sorted(query.categories or ()),
                  "groups": sorted(query.groups or ()), "kinds": sorted(query.kinds or ())}
        return self._envelope("search", session, None, inputs, payload)

    def benefit(self, benefit_id: str, session: Session) -> dict:
        benefit = self.registry.benefits.get(benefit_id)
        if benefit is None:
            raise KeyError(benefit_id)
        payload = {"item": {**self.listing(benefit), "rule": benefit.rule, "ledger_ref": benefit.ledger_ref,
                            "content_hash": benefit.content_hash,
                            "rule_leads": [self.registry.rule_leads[i] for i in benefit.lead_ids]}}
        return self._envelope("benefit", session, None, {"benefit_id": benefit_id}, payload)

    # ── writes (ApprovalGate first) ────────────────────────────────────────
    def create_grant(self, request: Mapping, session: Session, now: datetime) -> dict:
        source_agent = request.get("source_agent")
        keys = request.get("fact_keys") or []
        if not isinstance(source_agent, str) or not isinstance(keys, list):
            raise RequestError("source_agent is text and fact_keys is a list")
        span = (f"{request.get('hours') or self.registry.governance['grants']['session_max_hours']} hours"
                if session.mode == "A" else f"{request.get('days') or self.registry.governance['grants']['default_days']} days")
        consent = consent_text(self.manifests, source_agent, keys, span)
        self.approval.require("create_grant", request.get("confirm"), consent)
        try:
            grant = new_grant(self.manifests, self.registry.governance, tenant_ref=session.tenant_ref,
                              source_agent=source_agent, fact_keys=keys, purpose=request.get("purpose", "benefit_matching"),
                              mode=session.mode, now=now, days=request.get("days"), hours=request.get("hours"))
        except GrantError as exc:
            raise RequestError(f"{exc.reason}: {exc}") from None
        stored = session.grants.add(grant)
        session.ledger.append(tenant_ref=session.tenant_ref, occurred_at=now, event="GRANT_CREATED",
                              requester=VAULT_AGENT_ID, source_agent=grant.source_agent, purpose=grant.purpose,
                              fact_keys=grant.fact_keys, grant_id=stored.grant_id)
        return {"grant": stored.view(now), "consent_text": consent}

    def revoke_grant(self, grant_id: str, session: Session, now: datetime) -> dict:
        grant = session.grants.revoke(session.tenant_ref, grant_id, now)
        if grant is None:
            raise KeyError(grant_id)
        session.ledger.append(tenant_ref=session.tenant_ref, occurred_at=now, event="GRANT_REVOKED",
                              requester=VAULT_AGENT_ID, source_agent=grant.source_agent, purpose=grant.purpose,
                              fact_keys=grant.fact_keys, grant_id=grant.grant_id)
        return {"grant": grant.view(now)}

    def grants(self, session: Session, now: datetime) -> dict:
        return {"grants": [g.view(now) for g in session.grants.list(session.tenant_ref)]}

    def ledger(self, session: Session) -> dict:
        entries = session.ledger.entries(session.tenant_ref)
        ok, bad = session.ledger.verify(session.tenant_ref)
        return {"entries": [e.view() for e in entries], "chain_ok": ok, "first_bad_seq": bad}

    def save_benefit(self, request: Mapping, session: Session) -> dict:
        if session.mode != "B" or session.saved is None:
            raise ModeError("saving needs a private account (Mode B)")
        benefit = self.registry.benefits.get(request.get("benefit_id"))
        if benefit is None:
            raise KeyError(request.get("benefit_id"))
        status = request.get("status", "INTERESTED")
        if status not in SAVED_STATUSES:
            raise RequestError(f"status is one of {', '.join(SAVED_STATUSES)}")
        self.approval.require("save_benefit", request.get("confirm"),
                              f"Save \"{benefit.title}\" to your list. VetBuddy files nothing for you.")
        return {"saved": session.saved.save(session.tenant_ref, benefit.benefit_id, status, benefit.content_hash)}

    def saved(self, session: Session) -> dict:
        if session.mode != "B" or session.saved is None:
            raise ModeError("saved benefits need a private account (Mode B)")
        rows = []
        for row in session.saved.saved(session.tenant_ref):
            benefit = self.registry.benefits.get(row["benefit_id"])
            rows.append({**row, "retired": benefit is None,
                         "changed_since_saved": benefit is not None and benefit.content_hash != row["content_hash_at_save"],
                         "title": benefit.title if benefit else None})
        return {"saved": rows}
