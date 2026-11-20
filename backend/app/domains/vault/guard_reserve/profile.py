"""Guard & Reserve answers: validation, classification, derived vault facts and rule-lead checks.

Everything here is deterministic and reads only the authored policy and the
Operation Sentinel dataset. Classification restates what the dataset says
about a component, a duty status and an authority; the rule-lead checks
restate each lead's own condition. Neither is a benefit determination: the
outcomes use the v6 vocabulary and every check carries the lead's status.

The governing rule (Sentinel): duty counts by the legal authority printed on
the orders, never by the mission and never by component alone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

from ..facts import Fact, FactSet
from .policy import GuardReservePolicy

UNKNOWN_AUTHORITY = "unknown"
GR_KEYS = ("gr_component", "duty_status", "order_authorities", "qualifying_days")


class ProfileError(ValueError):
    """A Guard & Reserve answer that is not allowed; the API answers 422."""


@dataclass(frozen=True)
class GuardReserveProfile:
    gr_component: Optional[str] = None
    duty_status: Optional[str] = None
    order_authorities: Tuple[str, ...] = ()
    authorities_unknown: bool = False
    qualifying_days: Optional[int] = None
    unsure: FrozenSet[str] = frozenset()

    def canonical(self) -> dict:
        return {"gr_component": self.gr_component, "duty_status": self.duty_status,
                "order_authorities": list(self.order_authorities), "authorities_unknown": self.authorities_unknown,
                "qualifying_days": self.qualifying_days, "unsure": sorted(self.unsure)}

    def answered(self) -> List[str]:
        out = [k for k in ("gr_component", "duty_status") if getattr(self, k) is not None]
        if self.order_authorities or self.authorities_unknown:
            out.append("order_authorities")
        if self.qualifying_days is not None:
            out.append("qualifying_days")
        return out


def parse(raw: Any, policy: GuardReservePolicy) -> GuardReserveProfile:
    """Validate the person's Guard & Reserve answers against the Sentinel vocabulary."""
    if raw is None:
        raw = {}
    if not isinstance(raw, Mapping):
        raise ProfileError("guard_reserve is an object")
    unknown = sorted(set(raw) - set(GR_KEYS) - {"unsure"})
    if unknown:
        raise ProfileError(f"unknown Guard & Reserve answer: {', '.join(unknown)}")
    unsure = raw.get("unsure") or []
    if not isinstance(unsure, list) or not set(unsure) <= set(GR_KEYS) or not set(unsure) <= set(raw):
        raise ProfileError("guard_reserve.unsure lists keys that appear in guard_reserve")

    component = raw.get("gr_component")
    if component is not None and component not in policy.components:
        raise ProfileError(f"gr_component must be one of {', '.join(policy.components)}")
    status = raw.get("duty_status")
    if status is not None and status not in policy.statuses:
        raise ProfileError(f"duty_status must be one of {', '.join(policy.statuses)}")
    comp = policy.components.get(component) if component else None
    if status and comp and policy.statuses[status].guard_only and not comp.guard:
        raise ProfileError(f"{policy.statuses[status].label} is a National Guard status; "
                           f"{comp.label} is not a Guard component")

    authorities = raw.get("order_authorities") or []
    if not isinstance(authorities, list) or not all(isinstance(a, str) for a in authorities):
        raise ProfileError("order_authorities is a list of authority ids")
    authorities_unknown = UNKNOWN_AUTHORITY in authorities
    ids = tuple(sorted(dict.fromkeys(a for a in authorities if a != UNKNOWN_AUTHORITY)))
    bad = [a for a in ids if a not in policy.authorities]
    if bad:
        raise ProfileError(f"unknown authority: {', '.join(bad)}")
    if comp:
        for aid in ids:
            authority = policy.authorities[aid]
            if authority.guard_only and not comp.guard:
                raise ProfileError(f"{authority.citation} ({authority.label}) applies only to the National Guard")
            if authority.coast_guard_only and not comp.coast_guard:
                raise ProfileError(f"{authority.citation} applies only to the Coast Guard Reserve")

    days = raw.get("qualifying_days")
    if days is not None:
        low, high = policy.days_range
        if isinstance(days, bool) or not isinstance(days, int) or not low <= days <= high:
            raise ProfileError(f"qualifying_days must be a whole number from {low} to {high}")
    return GuardReserveProfile(component, status, ids, authorities_unknown, days, frozenset(unsure))


@dataclass
class Derivation:
    facts: FactSet
    derived: List[dict] = field(default_factory=list)
    conflicts: List[dict] = field(default_factory=list)
    caveat_ids: Tuple[str, ...] = ()


def derive(profile: GuardReserveProfile, facts: FactSet, policy: GuardReservePolicy) -> Derivation:
    """Turn Guard & Reserve answers into vault facts. An answer the person gave always wins."""
    wanted: Dict[str, Tuple[Any, str]] = {}
    caveats: Tuple[str, ...] = ()
    if profile.gr_component:
        component = policy.components[profile.gr_component]
        wanted["component"] = ("guard" if component.guard else "reserve", "gr_component")
    if profile.duty_status:
        entry = policy.derivation[profile.duty_status]
        for key, value in entry["facts"].items():
            wanted[key] = (value, "duty_status")
        caveats = entry["caveats"]
    out = FactSet(dict(facts.facts))
    derived, conflicts = [], []
    for key in sorted(wanted):
        value, basis = wanted[key]
        if facts.has(key):
            if facts.get(key) != value:
                conflicts.append({"fact_key": key, "answered": facts.get(key), "derived": value, "from": basis,
                                  "kept": "answered"})
            continue
        certain = basis not in profile.unsure
        out.put(Fact(key, value, "derived", certain, None))
        derived.append({"fact_key": key, "value": value, "from": basis, "certain": certain})
    return Derivation(out, derived, conflicts, caveats)


def classify(profile: GuardReserveProfile, policy: GuardReservePolicy) -> dict:
    """What the Sentinel dataset says about these answers. A restatement, not a determination."""
    component = policy.components.get(profile.gr_component) if profile.gr_component else None
    status = policy.statuses.get(profile.duty_status) if profile.duty_status else None
    authorities = [policy.authorities[a] for a in profile.order_authorities]
    qualifying = [a for a in authorities if a.qualifies_ch33]
    return {
        "governing_rule": policy.governing_rule,
        "component": None if component is None else
        {"id": component.component_id, "label": component.label, "short": component.short,
         "vault_component": "guard" if component.guard else "reserve"},
        "duty_status": None if status is None else
        {"id": status.status_id, "label": status.label, "sub": status.sub,
         "selected_reserve": status.selected_reserve, "tuition_assistance_status": status.fta_eligible},
        "agr": None if status is None else status.status_id in ("agr32", "agr10"),
        "agr_title": {"agr32": "32", "agr10": "10"}.get(profile.duty_status),
        "authorities": [{"id": a.authority_id, "citation": a.citation, "label": a.label,
                         "counts_toward_post_9_11_gi_bill": a.qualifies_ch33, "tier_caveat": a.tier_caveat}
                        for a in authorities],
        "authorities_unknown": profile.authorities_unknown,
        "has_post_9_11_authority": (None if not authorities else bool(qualifying)),
    }


def _publish(outcome: str, lead_status: str, policy_name: str, reasons: List[str]) -> str:
    """The vault's own order of checks, applied to a rule lead."""
    if outcome in ("PRELIMINARY_MATCH", "NEEDS_INFORMATION"):
        if lead_status == "SUPERSEDED":
            reasons.append("RECORD_SUPERSEDED")
            return "SOURCE_STALE"
        if lead_status == "CONTESTED":
            reasons.append("RECORD_CONTESTED")
            return "CONFLICTING_AUTHORITY"
        if outcome == "PRELIMINARY_MATCH" and policy_name == "verified_only" and lead_status != "VERIFIED":
            reasons.append("RECORD_NOT_VERIFIED")
            return "HUMAN_REVIEW_REQUIRED"
    return outcome


def lead_checks(profile: GuardReserveProfile, facts: FactSet, policy: GuardReservePolicy, registry,
                publish_policy: str) -> List[dict]:
    """Check the Sentinel rule leads the policy names against the person's answers."""
    out = []
    status = policy.statuses.get(profile.duty_status) if profile.duty_status else None
    for lead_id, spec in policy.lead_checks.items():
        lead = registry.rule_leads[lead_id]
        reasons: List[str] = []
        caveats: List[str] = []
        needed: List[dict] = []
        outcome: Optional[str] = None
        if spec.get("listed_only"):
            continue
        if "threshold_days" in spec:
            authorities = [policy.authorities[a] for a in profile.order_authorities]
            if any(a.tier_caveat for a in authorities):
                caveats.append("tier_caveat")
            if profile.authorities_unknown or not authorities:
                caveats.append("authority_from_orders")
            if profile.qualifying_days is None:
                outcome = "NEEDS_INFORMATION"
                reasons.append("ANSWERS_MISSING")
                needed.append({"fact_key": "qualifying_days", "question": policy.questions["qualifying_days"],
                               "data_class": "V1", "can_answer_here": True})
            elif authorities and not any(a.qualifies_ch33 for a in authorities) and profile.qualifying_days > 0:
                outcome = "HUMAN_REVIEW_REQUIRED"
                reasons.append("DAYS_WITHOUT_QUALIFYING_AUTHORITY")
            elif profile.qualifying_days >= spec["threshold_days"]:
                outcome = "PRELIMINARY_MATCH"
                reasons.append("ENCODED_CONDITIONS_MET")
            else:
                outcome = "DOES_NOT_MEET_ENCODED_RULES"
                reasons.append("ENCODED_CONDITION_NOT_MET")
                if profile.qualifying_days >= spec["near_threshold_from"]:
                    caveats.append("near_threshold")
            if outcome == "PRELIMINARY_MATCH" and "qualifying_days" in profile.unsure:
                outcome = "NEEDS_EVIDENCE"
                reasons.append("DEPENDS_ON_UNSURE_ANSWERS")
        elif spec.get("needs_selected_reserve") or spec.get("needs_fta_status"):
            if status is None:
                outcome = "NEEDS_INFORMATION"
                reasons.append("ANSWERS_MISSING")
                needed.append({"fact_key": "duty_status", "question": policy.questions["duty_status"],
                               "data_class": "V1", "can_answer_here": True})
            else:
                fits = status.selected_reserve if spec.get("needs_selected_reserve") else status.fta_eligible
                outcome = "PRELIMINARY_MATCH" if fits else "DOES_NOT_MEET_ENCODED_RULES"
                reasons.append("ENCODED_CONDITIONS_MET" if fits else "ENCODED_CONDITION_NOT_MET")
                if not status.selected_reserve:
                    caveats.append("not_selected_reserve")
                if fits and "duty_status" in profile.unsure:
                    outcome = "NEEDS_EVIDENCE"
                    reasons.append("DEPENDS_ON_UNSURE_ANSWERS")
        elif spec.get("applies_without_federal_active_duty"):
            days = facts.get("active_duty_days")
            component = facts.get("component")
            applies = component in ("guard", "reserve") and (days is None or days < 181)
            out.append({"lead_id": lead_id, "kind": "notice", "applies": applies, "topic": lead["topic"],
                        "citation": lead["citation"], "lead": lead["lead"], "record_status": lead["record_status"]})
            continue
        elif spec.get("contested"):
            outcome = "CONFLICTING_AUTHORITY"
            reasons.append("RECORD_CONTESTED")
        outcome = _publish(outcome, lead["record_status"], publish_policy, reasons)
        out.append({
            "lead_id": lead_id, "kind": "rule_lead_check", "outcome": outcome, "topic": lead["topic"],
            "citation": lead["citation"], "lead": lead["lead"], "lead_caveat": lead["caveat"],
            "record_status": lead["record_status"], "reasons": reasons, "facts_needed": needed,
            "caveats": [{"id": c, "text": policy.caveats[c]} for c in dict.fromkeys(caveats)],
        })
    return out
