"""The deterministic matcher.

Given what a person has told the vault (and what it pulled with their grant),
the matcher reports, for every record in scope, what the encoded rule says,
using only the v6 outcomes:

* PRELIMINARY_MATCH: the facts given fit every encoded condition.
* NEEDS_EVIDENCE: they fit only because of answers the person marked unsure.
* NEEDS_INFORMATION: an unanswered question could change the result.
* DOES_NOT_MEET_ENCODED_RULES: the facts given miss an encoded condition. It
  says nothing about eligibility; the agency decides that.
* SOURCE_STALE: the record's page was read longer ago than the review period.
* CONFLICTING_AUTHORITY: the record is CONTESTED.
* HUMAN_REVIEW_REQUIRED: the facts may fit, but the record cannot be shown as
  a match (not verified under the verified_only policy, link only seen in
  search, illustrative data, or a link off the egress allowlist). It always
  carries the official link so the person can read the source.

Nothing here calls a model or the network. The same registry, facts and
options always give the same output, and the envelope carries hashes that
prove it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from .facts import CATALOG, DISCHARGE_REVIEW, PSEUDO_KEYS, FactSet, facts_for_tokens, resolver, within_ceiling
from .guards import CitationValidator
from .registry import Benefit, VaultRegistry
from .rules import evaluate, tokens
from .tri import Tri
from .vocab import CATEGORY_LABELS, JURISDICTIONS, OUTCOMES

OUTCOME_ORDER = {name: index for index, name in enumerate(
    ("PRELIMINARY_MATCH", "NEEDS_EVIDENCE", "NEEDS_INFORMATION", "HUMAN_REVIEW_REQUIRED",
     "CONFLICTING_AUTHORITY", "SOURCE_STALE", "DOES_NOT_MEET_ENCODED_RULES"))}
if set(OUTCOME_ORDER) != set(OUTCOMES):  # pragma: no cover - import-time pin
    raise RuntimeError("matcher outcome order does not cover the v6 outcome set")

STATE_TRAP_MIN_DAYS = 181


@dataclass(frozen=True)
class MatchOptions:
    as_of: date
    environment: Optional[str] = None
    mode: str = "A"
    jurisdictions: Optional[Tuple[str, ...]] = None
    categories: Optional[FrozenSet[str]] = None
    kinds: Optional[FrozenSet[str]] = None
    include_non_matches: bool = False

    def canonical(self) -> dict:
        return {
            "as_of": self.as_of.isoformat(),
            "environment": self.environment,
            "mode": self.mode,
            "jurisdictions": list(self.jurisdictions) if self.jurisdictions else None,
            "categories": sorted(self.categories) if self.categories else None,
            "kinds": sorted(self.kinds) if self.kinds else None,
            "include_non_matches": self.include_non_matches,
        }


@dataclass
class MatchResult:
    items: List[dict]
    counts: Dict[str, int]
    scope: Tuple[str, ...]
    policy: str
    evaluated: int


class Matcher:
    def __init__(self, registry: VaultRegistry):
        self.registry = registry
        self.citations = CitationValidator(registry.governance["egress_allowlist"])
        self.stale_after = int(registry.governance["review"]["stale_after_days"])

    # ── scope ──────────────────────────────────────────────────────────────
    def scope(self, facts: FactSet, requested: Optional[Sequence[str]] = None) -> Tuple[str, ...]:
        """Federal records plus the places that matter for this person.

        A nonresident stationed in a state, or a member of another state's
        Guard, can still use some of that state's benefits, so the duty
        station and Guard state are in scope along with the residence.
        """
        if requested:
            bad = [code for code in requested if code not in JURISDICTIONS]
            if bad:
                raise ValueError(f"unknown jurisdiction {', '.join(bad)}")
            ordered = list(dict.fromkeys(requested))
        else:
            ordered = ["US"] + [facts.get(k) for k in ("residence_state", "duty_station_state", "guard_state")
                                if facts.get(k)]
        return tuple(dict.fromkeys(ordered))

    # ── one record ─────────────────────────────────────────────────────────
    def evaluate(self, benefit: Benefit, facts: FactSet, policy: str, options: MatchOptions) -> dict:
        resolve = resolver(facts, benefit.jurisdiction)
        value, missing = evaluate(benefit.node, resolve)
        reasons: List[str] = []
        to_document: Tuple[str, ...] = ()
        if value is Tri.TRUE:
            uncertain = facts.uncertain_keys()
            if uncertain:
                firm_value, _ = evaluate(benefit.node, resolver(facts.without(uncertain), benefit.jurisdiction))
                if firm_value is not Tri.TRUE:
                    outcome = "NEEDS_EVIDENCE"
                    reasons.append("DEPENDS_ON_UNSURE_ANSWERS")
                    to_document = tuple(sorted(uncertain & self._rule_fact_keys(benefit)))
                else:
                    outcome = "PRELIMINARY_MATCH"
            else:
                outcome = "PRELIMINARY_MATCH"
            reasons.insert(0, "ENCODED_CONDITIONS_MET")
        elif value is Tri.UNKNOWN:
            outcome = "NEEDS_INFORMATION"
            reasons.append("ANSWERS_MISSING")
        else:
            outcome = "DOES_NOT_MEET_ENCODED_RULES"
            reasons.append("ENCODED_CONDITION_NOT_MET")

        source = self.registry.sources[benefit.source_id]
        fits_or_open = outcome in ("PRELIMINARY_MATCH", "NEEDS_EVIDENCE", "NEEDS_INFORMATION")
        link_ok = self.citations.ok(benefit.official_url)
        if fits_or_open:
            if benefit.record_status == "SUPERSEDED":
                outcome = "SOURCE_STALE"
                reasons.append("RECORD_SUPERSEDED")
            elif benefit.record_status == "CONTESTED":
                outcome = "CONFLICTING_AUTHORITY"
                reasons.append("RECORD_CONTESTED")
            elif self._stale(source, options.as_of):
                outcome = "SOURCE_STALE"
                reasons.append("SOURCE_OLDER_THAN_REVIEW_PERIOD")
            elif not link_ok:
                outcome = "HUMAN_REVIEW_REQUIRED"
                reasons.append("LINK_NOT_ON_ALLOWLIST")
            elif benefit.official_url_status == "SEEN_IN_SEARCH" or benefit.record_status in ("ILLUSTRATIVE", "HEURISTIC"):
                if outcome != "NEEDS_INFORMATION":
                    outcome = "HUMAN_REVIEW_REQUIRED"
                reasons.append("SOURCE_NOT_READ")
            elif policy == "verified_only" and benefit.record_status != "VERIFIED" and outcome != "NEEDS_INFORMATION":
                outcome = "HUMAN_REVIEW_REQUIRED"
                reasons.append("RECORD_NOT_VERIFIED")

        caveat_ids = list(benefit.caveat_ids)
        if benefit.kind == "COMMERCIAL_DEAL":
            caveat_ids.append("commercial")
        elif benefit.kind == "NONPROFIT_PROGRAM":
            caveat_ids.append("nonprofit")
        if benefit.official_url_status == "SEEN_IN_SEARCH":
            caveat_ids.append("seen_in_search")
        if benefit.record_status != "VERIFIED":
            caveat_ids.append("not_verified")
        if source["tail_unread_chars"]:
            caveat_ids.append("tail_unread")
        if outcome == "NEEDS_EVIDENCE":
            caveat_ids.append("uncertain_facts")
        if outcome == "SOURCE_STALE":
            caveat_ids.append("superseded" if benefit.record_status == "SUPERSEDED" else "stale")
        if self._state_trap(benefit, facts) and outcome != "DOES_NOT_MEET_ENCODED_RULES":
            caveat_ids.append("state_definition_trap")
        caveat_ids = list(dict.fromkeys(caveat_ids))

        needed = []
        if outcome == "NEEDS_INFORMATION" or (value is Tri.UNKNOWN and outcome != "DOES_NOT_MEET_ENCODED_RULES"):
            needed = self._facts_needed(missing, options.mode)

        return {
            "benefit_id": benefit.benefit_id,
            "outcome": outcome,
            "title": benefit.title,
            "jurisdiction": benefit.jurisdiction,
            "jurisdiction_name": JURISDICTIONS[benefit.jurisdiction],
            "category": benefit.category,
            "category_label": CATEGORY_LABELS[benefit.category],
            "kind": benefit.kind,
            "groups": list(benefit.groups),
            "who_it_is_for": benefit.who_it_is_for,
            "value": benefit.value,
            "official_url": benefit.official_url if link_ok else None,
            "record_status": benefit.record_status,
            "verified_by": benefit.verified_by,
            "source": {
                "tier": benefit.source_tier,
                "page_status": source["page_status"],
                "url_status": benefit.official_url_status,
                "opened_on": source["opened_on"],
                "page_updated": source["page_updated"],
            },
            "rule": benefit.rule,
            "reasons": reasons,
            "facts_needed": needed,
            "facts_to_document": list(to_document),
            "caveats": [{"id": cid, "text": self.registry.caveats[cid]} for cid in caveat_ids],
            "lead_ids": list(benefit.lead_ids),
        }

    @staticmethod
    def _rule_fact_keys(benefit: Benefit) -> FrozenSet[str]:
        return facts_for_tokens(tokens(benefit.node))

    def _stale(self, source: dict, as_of: date) -> bool:
        stamp = source.get("opened_on") or source.get("seen_on")
        if not stamp:
            return True
        return (as_of - date.fromisoformat(stamp)).days > self.stale_after

    @staticmethod
    def _state_trap(benefit: Benefit, facts: FactSet) -> bool:
        if benefit.kind != "STATE_BENEFIT" or "vet" not in {t.name for t in tokens(benefit.node)}:
            return False
        if facts.get("component") not in ("guard", "reserve"):
            return False
        days = facts.get("active_duty_days")
        return days is None or days < STATE_TRAP_MIN_DAYS

    @staticmethod
    def _facts_needed(missing: Iterable[str], mode: str) -> List[dict]:
        out = []
        for key in sorted(missing):
            if key == DISCHARGE_REVIEW:
                out.append({"fact_key": key, "question": PSEUDO_KEYS[key], "data_class": "V2",
                            "can_answer_here": False})
                continue
            spec = CATALOG[key]
            allowed = within_ceiling(spec.data_class, mode) or (spec.session_only and mode == "B")
            out.append({"fact_key": key, "question": spec.question, "data_class": spec.data_class,
                        "can_answer_here": allowed})
        return out

    # ── many records ───────────────────────────────────────────────────────
    def candidates(self, scope: Sequence[str], options: MatchOptions) -> List[Benefit]:
        out = []
        for code in scope:
            for benefit in self.registry.by_jurisdiction.get(code, ()):
                if options.categories and benefit.category not in options.categories:
                    continue
                if options.kinds and benefit.kind not in options.kinds:
                    continue
                out.append(benefit)
        return out

    def match(self, facts: FactSet, options: MatchOptions) -> MatchResult:
        policy = self.registry.publish_policy(options.environment)
        scope = self.scope(facts, options.jurisdictions)
        scope_rank = {code: index for index, code in enumerate(scope)}
        items = [self.evaluate(b, facts, policy, options) for b in self.candidates(scope, options)]
        counts = {name: 0 for name in OUTCOMES}
        for item in items:
            counts[item["outcome"]] += 1
        if not options.include_non_matches:
            items = [i for i in items if i["outcome"] != "DOES_NOT_MEET_ENCODED_RULES"]
        items.sort(key=lambda i: (OUTCOME_ORDER[i["outcome"]], scope_rank[i["jurisdiction"]], i["category"], i["benefit_id"]))
        return MatchResult(items=items, counts=counts, scope=scope, policy=policy, evaluated=sum(counts.values()))
