"""Deterministic Mission Router: stage boundaries, routing, unknowns, determinism."""

from datetime import date, timedelta

import pytest

from app.kernel import vocab
from app.kernel.router import RouterInput, RouterInputError, compute_stage, compute_track, readiness, route

TODAY = date(2026, 10, 20)


def inp(**kw) -> RouterInput:
    base = dict(persona="veteran", branch="Army", component="separated", current_jurisdiction="AL",
                separation_date=TODAY - timedelta(days=400), goals=(), urgency="30_days")
    base.update(kw)
    return RouterInput(**base)


# Every boundary on both sides: (days until separation, expected stage).
BOUNDARIES = [
    (731, "in_service"), (730, "t_24_12m"), (366, "t_24_12m"), (365, "t_12_6m"), (181, "t_12_6m"),
    (180, "t_180_90d"), (91, "t_180_90d"), (90, "t_90_30d"), (31, "t_90_30d"), (30, "t_30d_sep"),
    (0, "t_30d_sep"), (-1, "day_0_30"), (-30, "day_0_30"), (-31, "day_31_90"), (-90, "day_31_90"),
    (-91, "month_3_12"), (-365, "month_3_12"), (-366, "year_1_2"), (-730, "year_1_2"), (-731, "year_2_3"),
    (-1095, "year_2_3"), (-1096, "year_3_5"), (-1825, "year_3_5"), (-1826, "ongoing"),
]


@pytest.mark.parametrize("days,stage", BOUNDARIES)
def test_stage_boundaries(days, stage):
    assert compute_stage(TODAY + timedelta(days=days), TODAY) == (stage, days)


def test_every_stage_has_a_label_and_is_reachable():
    reached = {s for _, s in BOUNDARIES} | {"unknown"}
    assert reached == set(vocab.STAGE_LABELS)


def test_missing_date_is_unknown_not_guessed():
    out = route(inp(separation_date=None), TODAY)
    assert out["stage"] == "unknown" and out["days_to_separation"] is None
    assert "FACT-DATE" in [t["template_id"] for t in out["tasks"]]
    assert "STAGE_UNKNOWN" in [n["code"] for n in out["notices"]]


def test_benefit_screening_notice_always_present():
    assert route(inp(), TODAY)["notices"][0]["code"] == "BENEFIT_SCREENING_NOT_AVAILABLE"


def test_guard_requires_authority_and_unknown_is_a_task():
    with pytest.raises(RouterInputError) as e:
        route(inp(persona="guard_reserve", component="national_guard"), TODAY)
    assert e.value.field == "legal_authority"
    out = route(inp(persona="guard_reserve", component="national_guard", legal_authority="unknown"), TODAY)
    ids = [t["template_id"] for t in out["tasks"]]
    assert "GR-AUTH" in ids and "GR-RECORD" in ids
    assert "guard_reserve" in out["lanes"] and out["track"] == "guard_reserve"
    assert "AUTHORITY_UNKNOWN" in [n["code"] for n in out["notices"]]


def test_two_personas_route_differently_and_reproducibly():
    a = inp(persona="guard_reserve", component="national_guard", legal_authority="title_32",
            separation_date=TODAY + timedelta(days=250), destination_jurisdiction="TX", goals=("education", "career"))
    b = inp(persona="veteran", branch="Navy", component="separated", current_jurisdiction="GA",
            separation_date=TODAY - timedelta(days=50), goals=("claims", "housing"))
    ra, rb = route(a, TODAY), route(b, TODAY)
    assert (ra["stage"], ra["track"]) == ("t_12_6m", "guard_reserve")
    assert (rb["stage"], rb["track"]) == ("day_31_90", "re_entry")
    assert {"REL-01", "HOU-01", "TAP-01"} <= {t["template_id"] for t in ra["tasks"]}
    assert "state_local" in ra["lanes"] and "state_local" not in rb["lanes"]
    assert {"CLM-01", "CLM-02", "HOU-02"} <= {t["template_id"] for t in rb["tasks"]}
    assert route(a, TODAY) == ra and route(b, TODAY) == rb


def test_input_hash_ignores_goal_order_and_duplicates():
    a = inp(goals=("career", "education", "career"))
    b = inp(goals=("education", "career"))
    assert a.input_hash() == b.input_hash()
    assert route(a, TODAY) == route(b, TODAY)


def test_tasks_sorted_by_priority_then_id_and_unique():
    out = route(inp(goals=tuple(vocab.GOALS), destination_jurisdiction="FL"), TODAY)
    keys = [(t["priority"], t["template_id"]) for t in out["tasks"]]
    assert keys == sorted(keys) and len(keys) == len(set(keys))


def test_stage_limited_tasks_drop_after_separation():
    before = route(inp(component="active_duty", persona="service_member", separation_date=TODAY + timedelta(days=100)), TODAY)
    after = route(inp(component="separated", separation_date=TODAY - timedelta(days=100)), TODAY)
    assert {"TAP-01", "COV-01"} <= {t["template_id"] for t in before["tasks"]}
    assert not {"TAP-01", "COV-01"} & {t["template_id"] for t in after["tasks"]}


def test_family_personas_track():
    assert compute_track(inp(persona="survivor")) == "spouse_family"
    assert compute_track(inp(component="medically_separated")) == "medical_separation"
    assert compute_track(inp(component="active_duty", persona="service_member", destination_jurisdiction="VA")) == "pcs"


@pytest.mark.parametrize("field,value", [
    ("persona", "general"), ("branch", "Starfleet"), ("component", "civilian"), ("current_jurisdiction", "ZZ"),
    ("destination_jurisdiction", "ZZ"), ("urgency", "yesterday"), ("legal_authority", "title_99"),
])
def test_invalid_values_rejected(field, value):
    with pytest.raises(RouterInputError) as e:
        route(inp(**{field: value}), TODAY)
    assert e.value.field == field


def test_unknown_goal_rejected():
    with pytest.raises(RouterInputError):
        route(inp(goals=("lottery",)), TODAY)


def test_readiness_is_per_dimension_not_a_score():
    rows = [{"readiness_dimension": "documents", "status": "done"},
            {"readiness_dimension": "career", "status": "todo"},
            {"readiness_dimension": "career", "status": "in_progress"},
            {"readiness_dimension": "education", "status": "cancelled"}]
    by = {r["dimension"]: r for r in readiness(rows)}
    assert by["documents"]["status"] == "ready"
    assert by["career"]["status"] == "in_progress" and by["career"]["total"] == 2
    assert by["education"]["status"] == "not_assessed"
    assert [r["dimension"] for r in readiness(rows)] == list(vocab.DIMENSIONS)
