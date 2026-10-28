"""Household derivation: facts for a spouse or child, built from the sponsor's.

A family member's benefits mostly turn on the sponsor (the service member or
veteran): is the sponsor serving, retired, rated 100% permanent and total,
and so on. Rather than asking the same questions twice, the vault derives the
sponsor facts for each household member from the sponsor's own fact set.

A derived fact keeps the data class of the fact it came from, so deriving can
never move information to a lower class. Facts the sponsor did not give stay
unknown for the member too.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple

from .facts import Fact, FactError, FactSet, validate_value

MEMBER_RELATIONSHIPS = ("spouse", "child")

# Facts a household member may state about themselves.
MEMBER_OWN_KEYS = frozenset({
    "age", "residence_state", "service_status", "component", "guard_state", "duty_station_state",
    "on_active_duty_orders", "active_duty_days", "wartime_service", "discharge", "va_rating",
    "rating_permanent_total", "individual_unemployability", "purple_heart", "medal_of_honor", "former_pow",
})


@dataclass(frozen=True)
class Member:
    member_id: str
    relationship: str
    own: Mapping[str, Any]


def _derive_sponsor(sponsor: FactSet) -> Dict[str, Fact]:
    out: Dict[str, Fact] = {}

    def put(key: str, value: Any, *source_keys: str) -> None:
        certain = all(sponsor.facts[k].certain for k in source_keys if k in sponsor.facts)
        out[key] = Fact(key, validate_value(key, value), "derived", certain)

    status = sponsor.get("service_status")
    if status in ("serving", "separated", "retired"):
        put("sponsor_status", status, "service_status")
    rating = sponsor.get("va_rating")
    if sponsor.has("va_rating"):
        put("sponsor_va_rating", rating, "va_rating")
        put("sponsor_service_connected", rating != "none", "va_rating")
        if rating == "none":
            put("sponsor_permanent_total", False, "va_rating")
            put("sponsor_unemployability", False, "va_rating")
    if sponsor.has("rating_permanent_total") and rating != "none":
        put("sponsor_permanent_total", bool(sponsor.get("rating_permanent_total")), "rating_permanent_total")
    if sponsor.has("individual_unemployability") and rating != "none":
        put("sponsor_unemployability", bool(sponsor.get("individual_unemployability")), "individual_unemployability")
    if sponsor.has("service_status"):
        # A living sponsor who is describing their own household did not die
        # in the line of duty and is not missing; family of a fallen member
        # use the survivor flow and state those facts themselves.
        put("sponsor_died_in_line_of_duty", False, "service_status")
        put("sponsor_pow_mia", False, "service_status")
        put("gold_star_family", False, "service_status")
    return out


def member_facts(sponsor: FactSet, member: Member) -> FactSet:
    """The fact set used to evaluate rules for one household member."""
    if member.relationship not in MEMBER_RELATIONSHIPS:
        raise FactError(f"a household member is a spouse or a child, not {member.relationship!r}")
    unknown = set(member.own) - MEMBER_OWN_KEYS
    if unknown:
        raise FactError(f"a household member cannot state {', '.join(sorted(unknown))}")
    facts = FactSet()
    for key, fact in _derive_sponsor(sponsor).items():
        facts.put(fact)
    facts.put(Fact("relationship", member.relationship, "self_attested"))
    if "residence_state" not in member.own and sponsor.has("residence_state"):
        source = sponsor.facts["residence_state"]
        facts.put(Fact("residence_state", source.value, "derived", source.certain))
    # A family member's duty station is the serving sponsor's (the stn token reads it that way).
    if ("duty_station_state" not in member.own and sponsor.get("service_status") == "serving"
            and sponsor.has("duty_station_state")):
        source = sponsor.facts["duty_station_state"]
        facts.put(Fact("duty_station_state", source.value, "derived", source.certain))
    if "service_status" not in member.own:
        facts.put(Fact("service_status", "never_served", "derived", False))
    for key, value in member.own.items():
        facts.put(Fact(key, validate_value(key, value), "self_attested"))
    return facts


def parse_members(items) -> Tuple[Member, ...]:
    members = []
    seen = set()
    for index, item in enumerate(items or ()):
        if not isinstance(item, Mapping):
            raise FactError("each household member is an object")
        member_id = str(item.get("member_id") or f"member-{index + 1}")
        if member_id in seen:
            raise FactError(f"duplicate member_id {member_id!r}")
        seen.add(member_id)
        own = dict(item.get("facts") or {})
        members.append(Member(member_id, str(item.get("relationship", "")), own))
    if len(members) > 12:
        raise FactError("at most 12 household members")
    return tuple(members)
