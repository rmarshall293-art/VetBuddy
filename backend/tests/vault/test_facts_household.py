"""The fact catalog, data classes, token semantics and household derivation."""
from __future__ import annotations

import pytest

from app.domains.vault.facts import (CATALOG, DISCHARGE_REVIEW, Fact, FactError, FactSet, resolver,
                                     validate_value, within_ceiling)
from app.domains.vault.household import Member, member_facts, parse_members
from app.domains.vault.rules import evaluate, parse
from app.domains.vault.tri import Tri
from app.domains.vault.vocab import DATA_CLASSES, NEVER_PULLABLE

T, U, F = Tri.TRUE, Tri.UNKNOWN, Tri.FALSE


def tok(facts, text, jur="TX"):
    return evaluate(parse(text), resolver(FactSet.from_mapping(facts), jur))


@pytest.mark.parametrize("key,value", [
    ("residence_state", "US"), ("residence_state", "XX"), ("service_status", "veteran"), ("va_rating", 55),
    ("va_rating", 110), ("va_rating", True), ("age", -1), ("age", "40"), ("purple_heart", "yes"), ("nope", 1)])
def test_bad_values_are_refused(key, value):
    with pytest.raises(FactError):
        validate_value(key, value)


def test_good_values_pass():
    assert validate_value("va_rating", "none") == "none"
    assert validate_value("va_rating", 70) == 70
    assert validate_value("residence_state", "GU") == "GU"
    assert validate_value("severe_disability", False) is False


def test_catalog_classes():
    assert all(spec.data_class in DATA_CLASSES for spec in CATALOG.values())
    assert CATALOG["va_rating"].data_class == "V2"
    assert CATALOG["residence_state"].data_class == "V1"
    sev = CATALOG["severe_disability"]
    assert sev.data_class == "V4" and sev.session_only and not sev.pullable
    for spec in CATALOG.values():
        if spec.data_class in NEVER_PULLABLE:
            assert not spec.pullable
    assert "income" not in " ".join(CATALOG)
    assert within_ceiling("V1", "A") and not within_ceiling("V2", "A") and within_ceiling("V2", "B")
    assert not within_ceiling("V1", "C")


def test_mode_ceilings_drop_facts():
    facts = FactSet.from_mapping({"residence_state": "TX", "va_rating": 100, "severe_disability": True})
    a, dropped_a = facts.limited_to("A")
    assert set(a.keys()) == {"residence_state"} and dropped_a == {"va_rating", "severe_disability"}
    b, dropped_b = facts.limited_to("B")
    assert set(b.keys()) == {"residence_state", "va_rating", "severe_disability"} and not dropped_b


def test_unsure_facts_are_tracked():
    facts = FactSet.from_mapping({"va_rating": 60, "age": 40}, uncertain=frozenset({"va_rating"}))
    assert facts.uncertain_keys() == {"va_rating"}
    assert not facts.without({"va_rating"}).has("va_rating")


def test_residence_tokens():
    assert tok({"residence_state": "TX"}, "res")[0] is T
    assert tok({"residence_state": "OK"}, "res")[0] is F
    assert tok({"residence_state": "OK"}, "nonres")[0] is T
    assert tok({"residence_state": "OK"}, "res", "US")[0] is T
    assert tok({"residence_state": "OK"}, "nonres", "US")[0] is F
    assert tok({}, "res")[1] == {"residence_state"}


def test_service_tokens():
    serving_guard = {"service_status": "serving", "component": "guard", "guard_state": "TX"}
    assert tok(serving_guard, "ng")[0] is T
    assert tok(serving_guard, "ng", "OK")[0] is F
    assert tok(serving_guard, "ngany", "OK")[0] is T
    assert tok(serving_guard, "rsv")[0] is F
    assert tok(serving_guard, "ad") == (U, frozenset({"on_active_duty_orders"}))
    assert tok({**serving_guard, "on_active_duty_orders": True}, "ad")[0] is T
    assert tok({"service_status": "serving", "component": "active"}, "ad")[0] is T
    assert tok({"service_status": "separated"}, "ad")[0] is F
    assert tok({"service_status": "retired", "component": "guard", "guard_state": "TX"}, "ngret")[0] is T
    # On a federal record any state's Guard counts, so the Guard state is not asked for.
    guard_no_state = {"service_status": "serving", "component": "guard"}
    assert tok(guard_no_state, "ng") == (U, frozenset({"guard_state"}))
    assert tok(guard_no_state, "ng", "US") == (T, frozenset())
    assert tok({"service_status": "retired", "component": "guard"}, "ngret", "US") == (T, frozenset())
    assert tok({"service_status": "retired"}, "vet & ret")[0] is T
    assert tok({"service_status": "serving", "duty_station_state": "TX"}, "stn")[0] is T
    assert tok({"service_status": "separated", "duty_station_state": "TX", "relationship": "self"}, "stn")[0] is F
    # A spouse or child of a member stationed in the state is covered by stn; the duty station is the member's.
    spouse = {"service_status": "never_served", "relationship": "spouse", "duty_station_state": "TX"}
    assert tok({**spouse, "sponsor_status": "serving"}, "stn") == (T, frozenset())
    assert tok({**spouse, "sponsor_status": "retired"}, "stn") == (F, frozenset())
    assert tok(spouse, "stn") == (U, frozenset({"sponsor_status"}))
    assert tok({"service_status": "separated", "duty_station_state": "TX"}, "stn") == (
        U, frozenset({"relationship", "sponsor_status"}))


def test_rating_and_discharge_tokens():
    assert tok({"va_rating": 0}, "sc")[0] is T
    assert tok({"va_rating": "none"}, "sc")[0] is F
    assert tok({"va_rating": "none"}, "pt")[0] is F
    assert tok({"va_rating": 70}, "r>=70")[0] is T and tok({"va_rating": 60}, "r>=70")[0] is F
    assert tok({"va_rating": 100}, "pt") == (U, frozenset({"rating_permanent_total"}))
    assert tok({"discharge": "general"}, "uhc")[0] is T and tok({"discharge": "general"}, "hon")[0] is F
    assert tok({"discharge": "dishonorable"}, "otd")[0] is F
    assert tok({"discharge": "other_than_honorable"}, "otd") == (U, frozenset({DISCHARGE_REVIEW}))
    assert tok({"discharge": "uncharacterized"}, "otd")[0] is T


def test_sponsor_died_token():
    assert tok({"relationship": "surviving_spouse"}, "spdec") == (T, frozenset())
    assert tok({"relationship": "child", "sponsor_status": "deceased"}, "spdec") == (T, frozenset())
    assert tok({"relationship": "child", "sponsor_died_in_line_of_duty": True}, "spdec") == (T, frozenset())
    assert tok({"relationship": "child", "sponsor_status": "retired", "sponsor_died_in_line_of_duty": False},
               "spdec") == (F, frozenset())
    assert tok({"relationship": "child"}, "spdec") == (U, frozenset({"sponsor_status", "sponsor_died_in_line_of_duty"}))
    assert tok({"relationship": "self"}, "spdec") == (F, frozenset())


def test_family_tokens():
    spouse = {"relationship": "spouse", "sponsor_status": "retired", "sponsor_va_rating": 100}
    assert tok(spouse, "sp & dep & spret & spr>=100")[0] is T
    assert tok(spouse, "ch | ss")[0] is F
    assert tok(spouse, "sppt") == (U, frozenset({"sponsor_permanent_total"}))
    # A person evaluated as themselves has no sponsor.
    assert tok({"relationship": "self"}, "spkia | spsm | spr>=10")[0] is F
    assert tok({"relationship": "surviving_spouse", "sponsor_died_in_line_of_duty": True}, "ss & spkia")[0] is T
    assert tok({"age": 25}, "age<26")[0] is T and tok({"age": 26}, "age<26")[0] is F


def test_household_derives_sponsor_facts():
    sponsor = FactSet.from_mapping({"residence_state": "TX", "service_status": "separated", "va_rating": 100,
                                    "rating_permanent_total": True, "relationship": "self"})
    child = member_facts(sponsor, Member("kid", "child", {"age": 19}))
    assert child.get("sponsor_status") == "separated"
    assert child.get("sponsor_va_rating") == 100 and child.get("sponsor_permanent_total") is True
    assert child.get("sponsor_service_connected") is True and child.get("sponsor_died_in_line_of_duty") is False
    assert child.get("residence_state") == "TX" and child.facts["residence_state"].provenance == "derived"
    assert child.get("service_status") == "never_served" and not child.facts["service_status"].certain
    value, _ = evaluate(parse("dep & (spkia | sppm | spr>=100 | spiu)"), resolver(child, "TX"))
    assert value is T
    for key, fact in child.facts.items():
        assert fact.data_class == CATALOG[key].data_class
    assert not child.has("duty_station_state")          # only a serving sponsor's duty station is shared


def test_household_shares_a_serving_sponsors_duty_station():
    sponsor = FactSet.from_mapping({"residence_state": "TX", "duty_station_state": "CO", "service_status": "serving",
                                    "component": "active", "relationship": "self"})
    spouse = member_facts(sponsor, Member("s", "spouse", {}))
    assert spouse.get("duty_station_state") == "CO" and spouse.facts["duty_station_state"].provenance == "derived"
    value, _ = evaluate(parse("stn & (ad | dep) & nonres"), resolver(spouse, "CO"))
    assert value is T


def test_household_member_limits():
    sponsor = FactSet.from_mapping({"service_status": "serving"})
    with pytest.raises(FactError):
        member_facts(sponsor, Member("x", "parent", {}))
    with pytest.raises(FactError):
        member_facts(sponsor, Member("x", "spouse", {"sponsor_va_rating": 100}))
    with pytest.raises(FactError):
        parse_members([{"member_id": "a", "relationship": "child"}, {"member_id": "a", "relationship": "child"}])
    with pytest.raises(FactError):
        parse_members([{"relationship": "child"}] * 13)
    assert parse_members([{"relationship": "spouse"}])[0].member_id == "member-1"


def test_unsure_sponsor_facts_stay_unsure():
    sponsor = FactSet.from_mapping({"service_status": "retired", "va_rating": 100}, uncertain=frozenset({"va_rating"}))
    spouse = member_facts(sponsor, Member("s", "spouse", {}))
    assert not spouse.facts["sponsor_va_rating"].certain
    assert spouse.facts["sponsor_status"].certain


def test_fact_provenance_is_checked():
    facts = FactSet()
    with pytest.raises(FactError):
        facts.put(Fact("age", 30, "guessed"))
