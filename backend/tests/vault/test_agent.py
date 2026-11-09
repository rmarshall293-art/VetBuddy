"""The Benefit Vault agent: pipeline guards, pulls with grants, household, search and envelopes."""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.domains.vault.agent import BenefitVaultAgent, ModeError, RequestError, Session
from app.domains.vault.envelope import ENVELOPE_NAME
from app.domains.vault.guards import ApprovalRequired, CrisisGate, LanguageGuard, OutputBlocked, PIIMinimizer

from vault_support import AS_OF, NOW, TENANT_A

TX_VET = {"residence_state": "TX", "service_status": "separated", "va_rating": 100, "discharge": "honorable"}


class Provider:
    def __init__(self, values):
        self.values = values
        self.calls = []

    def provide(self, tenant_ref, keys):
        self.calls.append(sorted(keys))
        return dict(self.values)


def account():
    return Session(mode="B", tenant_ref=TENANT_A)


def test_envelope_shape_and_determinism(dev_agent):
    env = dev_agent.match({"facts": TX_VET, "as_of": AS_OF}, account(), NOW)
    assert env["envelope"] == ENVELOPE_NAME and env["determination"] == "none"
    assert env["notice"].startswith("VetBuddy is an independent information and organization platform")
    assert env["registry"]["sha256"] == dev_agent.registry.sha256 and env["mode"] == "B"
    again = dev_agent.match({"facts": TX_VET, "as_of": AS_OF}, account(), NOW)
    assert again["hashes"] == env["hashes"]
    other = dev_agent.match({"facts": {**TX_VET, "va_rating": 90}, "as_of": AS_OF}, account(), NOW)
    assert other["hashes"]["inputs"] != env["hashes"]["inputs"]
    assert other["hashes"]["output"] != env["hashes"]["output"]
    assert env["subject"]["relationship"] == "self"


def test_mode_a_drops_v2_facts(dev_agent):
    env = dev_agent.match({"facts": TX_VET, "as_of": AS_OF}, Session(mode="A", tenant_ref="session-1"), NOW)
    assert env["subject"]["facts_not_used_in_this_mode"] == ["discharge", "va_rating"]
    assert [c["id"] for c in env["general_caveats"]] == ["mode_a_dropped"]
    assert all(q["data_class"] == "V1" or not q["can_answer_here"] for q in env["questions"])


def test_mode_c_is_unreachable():
    with pytest.raises(ModeError):
        Session(mode="C", tenant_ref="x")


def test_bad_requests(dev_agent):
    for request in ({"facts": {"va_rating": 55}}, {"facts": "x"}, {"facts": {}, "unsure": ["age"]},
                    {"facts": {}, "categories": ["NOPE"]}, {"facts": {}, "as_of": "yesterday"},
                    {"facts": {}, "jurisdictions": []}):
        with pytest.raises(RequestError):
            dev_agent.match(request, account(), NOW)


def test_severe_disability_is_used_but_never_echoed(dev_agent):
    env = dev_agent.match({"facts": {**TX_VET, "va_rating": 40, "severe_disability": True}, "as_of": AS_OF},
                          account(), NOW)
    combo = next(i for i in env["items"] if i["benefit_id"] == "tx.free-super-combo-for-disabled-veterans")
    assert combo["outcome"] == "PRELIMINARY_MATCH"
    assert "severe_disability" in env["subject"]["facts_used"]
    guest = dev_agent.match({"facts": {**TX_VET, "severe_disability": True}, "as_of": AS_OF},
                            Session(mode="A", tenant_ref="session-2"), NOW)
    assert "severe_disability" in guest["subject"]["facts_not_used_in_this_mode"]


def test_pull_with_a_grant_end_to_end(registry):
    provider = Provider({"service_status": "retired", "component": "guard", "guard_state": "TX",
                         "discharge": "honorable", "purple_heart": True, "secret": "x"})
    agent = BenefitVaultAgent(registry, providers={"service_profile_agent": provider}, environment="development")
    session = account()
    with pytest.raises(ApprovalRequired) as info:
        agent.create_grant({"source_agent": "service_profile_agent", "fact_keys": ["service_status"]}, session, NOW)
    assert "Service Profile" in info.value.consent_text
    created = agent.create_grant({"source_agent": "service_profile_agent", "confirm": True,
                                  "fact_keys": ["service_status", "component", "guard_state", "discharge"]},
                                 session, NOW)
    assert created["grant"]["state"] == "ACTIVE" and created["grant"]["scope"] == "account"
    env = agent.match({"facts": {"residence_state": "TX", "va_rating": 100}, "as_of": AS_OF}, session,
                      NOW + timedelta(minutes=1))
    pulled = {p["fact_key"] for p in env["subject"]["facts_pulled"]}
    assert pulled == {"service_status", "component", "guard_state", "discharge"}
    assert "purple_heart" not in env["subject"]["facts_used"]          # not granted, never delivered
    assert env["subject"]["pulls"][0]["allowed"] is True
    homestead = next(i for i in env["items"] if i["benefit_id"] == "tx.100-disabled-veteran-homestead-exemption")
    assert homestead["outcome"] == "PRELIMINARY_MATCH"
    ledger = agent.ledger(session)
    assert ledger["chain_ok"] and [e["event"] for e in ledger["entries"]] == ["GRANT_CREATED", "PULL_ALLOWED"]
    assert "retired" not in repr(ledger) and "honorable" not in repr(ledger)
    # Revoking stops pulls at once.
    agent.revoke_grant(created["grant"]["grant_id"], session, NOW + timedelta(minutes=2))
    later = agent.match({"facts": {"residence_state": "TX"}, "as_of": AS_OF}, session, NOW + timedelta(minutes=3))
    assert later["subject"]["facts_pulled"] == [] and later["subject"]["pulls"] == []
    assert [e["event"] for e in agent.ledger(session)["entries"]][-1] == "GRANT_REVOKED"


def test_pull_asks_only_for_facts_rules_need(registry):
    provider = Provider({"age": 40, "relationship": "self"})
    agent = BenefitVaultAgent(registry, providers={"household_agent": provider}, environment="development")
    session = account()
    agent.create_grant({"source_agent": "household_agent", "fact_keys": ["age", "relationship"], "confirm": True},
                       session, NOW)
    agent.match({"facts": {"residence_state": "TX", "service_status": "separated"}, "as_of": AS_OF,
                 "categories": ["PROPTAX"]}, session, NOW + timedelta(seconds=5))
    # relationship is already known (it defaults to self), so only age is asked for.
    assert provider.calls == [["age"]]


def test_keys_granted_in_separate_grants_are_all_pulled(registry):
    provider = Provider({"service_status": "serving", "component": "guard", "guard_state": "TX"})
    agent = BenefitVaultAgent(registry, providers={"service_profile_agent": provider}, environment="development")
    session = account()
    for second, keys in enumerate((["service_status"], ["component", "guard_state"])):
        agent.create_grant({"source_agent": "service_profile_agent", "fact_keys": keys, "confirm": True},
                           session, NOW + timedelta(seconds=second))
    env = agent.match({"facts": {"residence_state": "TX"}, "as_of": AS_OF}, session, NOW + timedelta(seconds=5))
    pulled = {p["fact_key"] for p in env["subject"]["facts_pulled"]}
    assert pulled == {"service_status", "component", "guard_state"}
    assert [sorted(p["fact_keys"]) for p in env["subject"]["pulls"]] == [["service_status"],
                                                                          ["component", "guard_state"]]
    assert provider.calls == [["service_status"], ["component", "guard_state"]]
    events = [e["event"] for e in agent.ledger(session)["entries"]]
    assert events == ["GRANT_CREATED", "GRANT_CREATED", "PULL_ALLOWED", "PULL_ALLOWED"]


def test_session_grants_stay_at_v1(dev_agent):
    session = Session(mode="A", tenant_ref="session-3")
    with pytest.raises(RequestError, match="CLASS_ABOVE_MODE_CEILING"):
        dev_agent.create_grant({"source_agent": "service_profile_agent", "fact_keys": ["discharge"], "confirm": True},
                               session, NOW)
    ok = dev_agent.create_grant({"source_agent": "service_profile_agent", "fact_keys": ["service_status"],
                                 "confirm": True, "hours": 4}, session, NOW)
    assert ok["grant"]["scope"] == "session"


def test_household(dev_agent):
    request = {"facts": TX_VET | {"rating_permanent_total": True}, "as_of": AS_OF,
               "members": [{"member_id": "spouse", "relationship": "spouse"},
                           {"member_id": "kid", "relationship": "child", "facts": {"age": 19}}]}
    env = dev_agent.household(request, account(), NOW)
    members = {m["member_id"]: m for m in env["members"]}
    for member_id in ("spouse", "kid"):
        ids = {i["benefit_id"]: i["outcome"] for i in members[member_id]["items"]}
        assert ids["tx.hazlewood-for-spouses-and-children"] == "PRELIMINARY_MATCH"
    assert members["kid"]["relationship"] == "child"
    kid_ids = {i["benefit_id"] for i in members["kid"]["items"]}
    assert "tx.hazlewood-legacy-for-children" in kid_ids
    with pytest.raises(RequestError):
        dev_agent.household({"facts": TX_VET, "members": []}, account(), NOW)
    with pytest.raises(RequestError):
        dev_agent.household({"facts": {**TX_VET, "relationship": "spouse"},
                             "members": [{"relationship": "child"}]}, account(), NOW)


def test_crisis_and_mst_gates(dev_agent):
    crisis = dev_agent.match({"facts": TX_VET, "note": "I don't want to live anymore"}, account(), NOW)
    assert crisis["kind"] == "crisis_floor" and crisis["crisis_floor"] is True
    numbers = " ".join(c.get("phone", "") for c in crisis["contacts"])
    assert "988" in numbers and "273-8255" not in numbers
    mst = dev_agent.search({"q": "he raped me in basic"}, account())
    assert mst["kind"] == "support_resources" and mst["narrative_not_processed"] is True
    ordinary = dev_agent.search({"q": "MST support"}, account())
    assert ordinary["kind"] == "search"


def test_crisis_floor_never_names_the_retired_number(tmp_path):
    bad = tmp_path / "floor.yaml"
    bad.write_text("contacts:\n  - {key: old, label: Old line, phone: '1-800-273-8255'}\nemergency: {label: x, phone: '911'}\n")
    with pytest.raises(ValueError):
        CrisisGate(bad)


def test_pii_minimizer():
    cleaned, removed = PIIMinimizer().minimize("my ssn 123-45-6789 email a.b@x.org call 334-555-1212 parks")
    assert "123" not in cleaned and "@" not in cleaned and "555" not in cleaned
    assert set(removed) == {"ssn", "email", "phone"} and cleaned.endswith("parks")


def test_search(dev_agent):
    env = dev_agent.search({"q": "park pass", "jurisdictions": ["US"]}, account())
    ids = [i["benefit_id"] for i in env["items"]]
    assert "us.america-the-beautiful-military-lifetime-pass" in ids[:5]
    tx = dev_agent.search({"q": "hunting license", "jurisdictions": ["TX"]}, account())
    assert tx["total"] >= 2 and all(i["jurisdiction"] == "TX" for i in tx["items"])
    pii = dev_agent.search({"q": "scholarship 123-45-6789"}, account())
    assert pii["query"] == "scholarship" and pii["identifiers_removed"] == ["ssn"]
    page = dev_agent.search({"q": "", "categories": ["DEALS"], "limit": 2}, account())
    assert page["total"] == 4 and len(page["items"]) == 2
    with pytest.raises(RequestError):
        dev_agent.search({"q": "x", "limit": 0}, account())
    with pytest.raises(RequestError):
        dev_agent.search({"q": "x", "jurisdictions": ["ZZ"]}, account())


def test_benefit_detail(dev_agent):
    env = dev_agent.benefit("us.post-9-11-gi-bill-chapter-33", account())
    item = env["item"]
    assert item["rule_leads"][0]["lead_id"] == "gr.ch33" and item["source"]["tier"] == 1
    assert item["ledger_ref"].startswith("federal/")
    with pytest.raises(KeyError):
        dev_agent.benefit("us.nothing-here", account())


def test_output_guard_blocks_prohibited_language(registry, monkeypatch):
    agent = BenefitVaultAgent(registry, environment="development")
    monkeypatch.setitem(registry.caveats, "not_verified", "Good news: you qualify for this benefit.")
    with pytest.raises(OutputBlocked):
        agent.match({"facts": TX_VET, "as_of": AS_OF}, account(), NOW)


def test_language_guard_normalizes_phrasing():
    guard = LanguageGuard()
    assert guard.violations("You are ELIGIBLE   for this!")
    assert guard.violations("This is guaranteed.")
    assert not guard.violations("Veterans rated 50% or more may apply.")


def test_saving_needs_an_account(dev_agent):
    with pytest.raises(ModeError):
        dev_agent.save_benefit({"benefit_id": "us.fry-scholarship", "confirm": True},
                               Session(mode="A", tenant_ref="session-4"))
