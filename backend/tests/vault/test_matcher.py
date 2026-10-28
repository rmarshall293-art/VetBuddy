"""The matcher: v6 outcomes, publish policy, caveats, scope and determinism."""
from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from app.domains.vault.facts import FactSet
from app.domains.vault.matcher import MatchOptions, Matcher
from app.domains.vault.registry import Review
from app.domains.vault.vocab import OUTCOMES

TX_VET_100 = {"residence_state": "TX", "service_status": "separated", "va_rating": 100,
              "discharge": "honorable", "relationship": "self"}
HOMESTEAD = "tx.100-disabled-veteran-homestead-exemption"


def opts(**kw):
    kw.setdefault("as_of", date(2026, 10, 27))
    return MatchOptions(**kw)


def item_for(result, benefit_id):
    return next(i for i in result.items if i["benefit_id"] == benefit_id)


@pytest.fixture(scope="module")
def matcher(registry):
    return Matcher(registry)


def run(matcher, facts, uncertain=frozenset(), **kw):
    kw.setdefault("mode", "B")
    return matcher.match(FactSet.from_mapping(facts, uncertain=uncertain), opts(**kw))


def test_preliminary_match_in_development(matcher):
    result = run(matcher, TX_VET_100, environment="development")
    item = item_for(result, HOMESTEAD)
    assert item["outcome"] == "PRELIMINARY_MATCH"
    assert item["reasons"] == ["ENCODED_CONDITIONS_MET"]
    assert item["official_url"].startswith("https://")
    assert {"not_verified"} <= {c["id"] for c in item["caveats"]}
    assert result.policy == "preview_unverified"


def test_production_shows_unverified_records_as_review_leads(matcher):
    result = run(matcher, TX_VET_100, environment="production")
    item = item_for(result, HOMESTEAD)
    assert item["outcome"] == "HUMAN_REVIEW_REQUIRED"
    assert "RECORD_NOT_VERIFIED" in item["reasons"]
    assert item["official_url"]
    assert result.counts["PRELIMINARY_MATCH"] == 0


def test_verified_record_matches_in_production(registry):
    benefit = registry.benefits[HOMESTEAD]
    reviewed = registry.with_reviews([Review(HOMESTEAD, "reviewer-01", "2026-10-28", benefit.content_hash)])
    result = Matcher(reviewed).match(FactSet.from_mapping(TX_VET_100), opts(environment="production"))
    item = item_for(result, HOMESTEAD)
    assert item["outcome"] == "PRELIMINARY_MATCH" and item["verified_by"] == "reviewer-01"
    assert "not_verified" not in {c["id"] for c in item["caveats"]}


def test_needs_information_lists_the_question(matcher):
    facts = {k: v for k, v in TX_VET_100.items() if k != "va_rating"}
    item = item_for(run(matcher, facts, environment="development"), HOMESTEAD)
    assert item["outcome"] == "NEEDS_INFORMATION"
    needed = {n["fact_key"]: n for n in item["facts_needed"]}
    assert set(needed) == {"va_rating", "individual_unemployability"}
    assert needed["va_rating"]["can_answer_here"] is True


def test_needs_information_in_mode_a_marks_v2_questions(matcher):
    facts = {"residence_state": "TX", "service_status": "separated", "relationship": "self"}
    item = item_for(run(matcher, facts, environment="development", mode="A"), HOMESTEAD)
    assert item["outcome"] == "NEEDS_INFORMATION"
    assert all(n["can_answer_here"] is False for n in item["facts_needed"] if n["data_class"] == "V2")


def test_needs_evidence_when_the_match_rests_on_unsure_answers(matcher):
    result = run(matcher, TX_VET_100, uncertain=frozenset({"va_rating"}), environment="development")
    item = item_for(result, HOMESTEAD)
    assert item["outcome"] == "NEEDS_EVIDENCE"
    assert item["facts_to_document"] == ["va_rating"]
    assert "uncertain_facts" in {c["id"] for c in item["caveats"]}
    # An unsure answer the rule does not depend on changes nothing.
    other = run(matcher, {**TX_VET_100, "age": 50}, uncertain=frozenset({"age"}), environment="development")
    assert item_for(other, HOMESTEAD)["outcome"] == "PRELIMINARY_MATCH"


def test_unanswered_alternative_keeps_a_record_open(matcher):
    """A 30% rating misses r>=100, but unemployability (iu) is still unanswered."""
    item = item_for(run(matcher, {**TX_VET_100, "va_rating": 30}, environment="development"), HOMESTEAD)
    assert item["outcome"] == "NEEDS_INFORMATION"
    assert [n["fact_key"] for n in item["facts_needed"]] == ["individual_unemployability"]


def test_does_not_meet_is_hidden_unless_asked(matcher):
    facts = {**TX_VET_100, "va_rating": 30, "individual_unemployability": False}
    hidden = run(matcher, facts, environment="development")
    assert HOMESTEAD not in {i["benefit_id"] for i in hidden.items}
    assert hidden.counts["DOES_NOT_MEET_ENCODED_RULES"] > 0
    shown = run(matcher, facts, environment="development", include_non_matches=True)
    assert item_for(shown, HOMESTEAD)["outcome"] == "DOES_NOT_MEET_ENCODED_RULES"


def test_source_stale_after_the_review_period(matcher):
    result = run(matcher, TX_VET_100, environment="development", as_of=date(2027, 6, 1))
    item = item_for(result, HOMESTEAD)
    assert item["outcome"] == "SOURCE_STALE"
    assert "stale" in {c["id"] for c in item["caveats"]}


def test_contested_and_superseded_records(registry):
    clone = registry.with_reviews([])
    clone.benefits[HOMESTEAD] = replace(clone.benefits[HOMESTEAD], record_status="CONTESTED")
    clone.benefits["tx.free-super-combo-for-disabled-veterans"] = replace(
        clone.benefits["tx.free-super-combo-for-disabled-veterans"], record_status="SUPERSEDED")
    clone._index()
    result = Matcher(clone).match(FactSet.from_mapping(TX_VET_100), opts(environment="development"))
    assert item_for(result, HOMESTEAD)["outcome"] == "CONFLICTING_AUTHORITY"
    superseded = item_for(result, "tx.free-super-combo-for-disabled-veterans")
    assert superseded["outcome"] == "SOURCE_STALE" and "superseded" in {c["id"] for c in superseded["caveats"]}


def test_seen_in_search_records_are_always_review_leads(matcher):
    result = run(matcher, {"service_status": "serving", "component": "active", "relationship": "self"},
                 environment="development")
    item = item_for(result, "us.waves-of-honor-seaworld-busch-gardens-and-partner-parks")
    assert item["outcome"] == "HUMAN_REVIEW_REQUIRED" and "SOURCE_NOT_READ" in item["reasons"]
    assert {"commercial", "seen_in_search"} <= {c["id"] for c in item["caveats"]}


def test_kind_caveats(matcher):
    result = run(matcher, {"service_status": "separated", "relationship": "self", "va_rating": 100,
                           "discharge": "honorable"}, environment="development")
    assert "commercial" in {c["id"] for c in item_for(result, "us.home-depot-military-discount")["caveats"]}
    spouse = run(matcher, {"relationship": "spouse", "sponsor_service_connected": True,
                           "sponsor_died_in_line_of_duty": False}, environment="development")
    assert "nonprofit" in {c["id"] for c in item_for(spouse, "us.folds-of-honor-military-scholarships")["caveats"]}


def test_state_definition_trap_for_drill_only_guard(matcher):
    facts = {"residence_state": "TX", "service_status": "separated", "component": "guard", "guard_state": "TX",
             "discharge": "honorable", "relationship": "self"}
    item = item_for(run(matcher, facts, environment="development"), "tx.hazlewood-act-for-veterans")
    assert item["outcome"] == "NEEDS_INFORMATION"
    assert "state_definition_trap" in {c["id"] for c in item["caveats"]}
    enough = item_for(run(matcher, {**facts, "active_duty_days": 400}, environment="development"),
                      "tx.hazlewood-act-for-veterans")
    assert enough["outcome"] == "PRELIMINARY_MATCH"
    assert "state_definition_trap" not in {c["id"] for c in enough["caveats"]}


def test_record_caveats_and_leads(matcher):
    facts = {"service_status": "serving", "component": "guard", "guard_state": "AL", "relationship": "self"}
    item = item_for(run(matcher, facts, environment="development"), "us.post-9-11-gi-bill-chapter-33")
    assert "guard_post911" in {c["id"] for c in item["caveats"]} and item["lead_ids"] == ["gr.ch33"]


def test_scope_includes_duty_station_and_guard_state(matcher):
    facts = FactSet.from_mapping({"residence_state": "AL", "duty_station_state": "GA", "guard_state": "TN",
                                  "service_status": "serving", "component": "guard"})
    assert matcher.scope(facts) == ("US", "AL", "GA", "TN")
    assert matcher.scope(facts, ["US", "WY"]) == ("US", "WY")
    with pytest.raises(ValueError):
        matcher.scope(facts, ["ZZ"])


def test_filters(matcher):
    result = run(matcher, TX_VET_100, environment="development", categories=frozenset({"PARKS", "PASS"}))
    assert result.items and {i["category"] for i in result.items} <= {"PARKS", "PASS"}
    deals = run(matcher, TX_VET_100, environment="development", kinds=frozenset({"COMMERCIAL_DEAL"}))
    assert deals.items and {i["kind"] for i in deals.items} == {"COMMERCIAL_DEAL"}


def test_outcomes_stay_in_the_v6_set_and_order_is_stable(matcher):
    first = run(matcher, TX_VET_100, environment="development", include_non_matches=True)
    second = run(matcher, TX_VET_100, environment="development", include_non_matches=True)
    assert [i["benefit_id"] for i in first.items] == [i["benefit_id"] for i in second.items]
    assert {i["outcome"] for i in first.items} <= set(OUTCOMES)
    assert sum(first.counts.values()) == first.evaluated == len(first.items)
    words = " ".join(i["outcome"] for i in first.items).lower()
    assert "approved" not in words and "eligible" not in words


def test_every_record_evaluates_without_error(matcher, registry):
    """Every rule in the registry runs against an empty, a veteran and a spouse fact set."""
    for facts in ({}, TX_VET_100, {"relationship": "spouse", "sponsor_status": "retired", "sponsor_va_rating": 100}):
        fs = FactSet.from_mapping(facts)
        for benefit in registry.benefits.values():
            item = matcher.evaluate(benefit, fs, "preview_unverified", opts())
            assert item["outcome"] in OUTCOMES
