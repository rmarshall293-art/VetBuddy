"""Reference data (data/reference): validation, API, guard, single authorship."""

import copy
import json

import pytest

from app import reference
from app.governance import language
from app.governance.language import check_text
from app.kernel import crisis


def _data():
    return copy.deepcopy(reference.load())


def test_corpus_loads_and_validates():
    d = reference.load()
    assert len(d["governance"]["agent_rules"]) == 22 and len(d["governance"]["tier0_rules"]) == 12
    assert len(d["transition_timeline"]["windows"]) == 12 and len(d["governance"]["legal_lane"]) == 8


@pytest.mark.parametrize("break_it,msg", [
    (lambda d: d["transition_timeline"]["windows"][0]["sources"].append("src.nowhere"), "unknown"),
    (lambda d: d["transition_timeline"]["windows"][0].update(status="VERIFIED"), "named reviewer"),
    (lambda d: d["transition_timeline"]["windows"][1].update(id=d["transition_timeline"]["windows"][0]["id"]), "duplicate"),
    (lambda d: d["governance"]["agent_rules"].pop(), "R1..R22"),
    (lambda d: d["governance"]["tier0_rules"][0].update(repo_status="DONE"), "status"),
    (lambda d: d["governance"]["legal_lane"][0].update(allowed="maybe"), "legal lane"),
    (lambda d: d["conflicts"]["conflicts"][0].update(readings=["one"]), "two or more"),
])
def test_validator_refuses_broken_data(break_it, msg):
    d = _data()
    break_it(d)
    with pytest.raises(reference.ReferenceDataError, match=msg):
        reference.validate(d)


def test_verified_needs_reviewer_and_date():
    d = _data()
    d["transition_timeline"]["windows"][0].update(status="VERIFIED", verified_by="Named Reviewer", verified_on="2026-10-21")
    reference.validate(d)


def test_nothing_is_verified_yet():
    tl = reference.load()["transition_timeline"]
    assert all(w.get("status", tl["default_status"]) != "VERIFIED" for w in tl["windows"])


def test_language_has_one_author():
    g = reference.governance()["language"]
    assert (language.STANDARD_DISCLAIMER, language.VSO_REFERRAL, language.FIND_REP_URL) == \
        (g["standard_disclaimer"], g["vso_referral_block"], g["vso_search_url"])


def test_crisis_floor_has_six_contacts_with_numbers():
    keys = [c["key"] for c in crisis.CRISIS_CONTACTS]
    assert keys == ["veterans_crisis_line", "988", "domestic_violence_hotline", "women_veterans_call_center",
                    "homeless_veterans_call_center", "dod_safe_helpline"]
    assert all(c["phone"] for c in crisis.CRISIS_CONTACTS)


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def test_all_reference_wording_passes_the_guard():
    # Conflicts hold contested readings quoted from sources, not VetBuddy's voice; everything else is our copy.
    d = reference.load()
    bad = [(name, v.excerpt) for name in ("governance", "sources", "transition_timeline")
           for s in _strings(d[name]) for v in check_text(s)]
    assert bad == []


def test_reference_api(guest_client):
    idx = guest_client.get("/api/v1/reference").json()
    assert set(idx["datasets"]) == set(reference.DATASETS) and idx["verified_rows"] == 0
    for name in reference.DATASETS:
        r = guest_client.get(f"/api/v1/reference/{name}")
        assert r.status_code == 200 and r.json() == json.loads(json.dumps(reference.load()[name]))
    assert guest_client.get("/api/v1/reference/../../etc/passwd").status_code == 404
    assert guest_client.get("/api/v1/reference/secrets").status_code == 404
    assert len(guest_client.get("/api/v1/crisis-resources").json()["contacts"]) == 6
