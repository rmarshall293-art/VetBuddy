"""The Guard & Reserve role of Benefits Intelligence (ADR 0011)."""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import timedelta
from pathlib import Path

import pytest
import yaml
from starlette.applications import Starlette
from starlette.testclient import TestClient

from app.domains.vault.agent import BenefitVaultAgent, RequestError, Session
from app.domains.vault.canonical import sha256_hex
from app.domains.vault.governance.manifests import ManifestError, ManifestSet
from app.domains.vault.guard_reserve import ROLE_ID
from app.domains.vault.guard_reserve import api as gr_api
from app.domains.vault.guard_reserve.agent import GuardReserveAgent
from app.domains.vault.guard_reserve.policy import POLICY_PATH, GuardReservePolicy, PolicyError, default_policy
from app.domains.vault.guard_reserve.profile import ProfileError, parse
from app.domains.vault.vocab import OUTCOMES

from vault_support import AS_OF, NOW, ROOT, TENANT_A

AGR32 = {"gr_component": "arng", "duty_status": "agr32", "order_authorities": ["a11", "a13"], "qualifying_days": 400}
AL = {"residence_state": "AL", "guard_state": "AL"}


def guest(ref="gr-guest"):
    return Session(mode="A", tenant_ref=ref)


@pytest.fixture(scope="module")
def dev_role(dev_agent):
    return GuardReserveAgent(dev_agent)


@pytest.fixture(scope="module")
def prod_role(prod_agent):
    return GuardReserveAgent(prod_agent)


def checks(env):
    return {c["lead_id"]: c for c in env["rule_lead_checks"]}


# ── governance alignment ────────────────────────────────────────────────────
def test_role_has_a_vault_manifest_that_cannot_pull_decide_or_expose(registry):
    manifest = next(a for a in registry.agents if a["agent_id"] == ROLE_ID)
    assert manifest["plane"] == 5 and manifest["exposes"] == []
    assert manifest["may_pull_from_agents"] is False and manifest["may_issue_determinations"] is False
    assert [a["agent_id"] for a in registry.agents if a["may_pull_from_agents"]] == ["benefits_intelligence_agent"]


def test_a_pulling_guard_reserve_manifest_is_refused(registry):
    items = copy.deepcopy(registry.agents)
    next(a for a in items if a["agent_id"] == ROLE_ID)["may_pull_from_agents"] = True
    with pytest.raises(ManifestError):
        ManifestSet(items)


def test_no_manifest_no_access(dev_agent):
    clone = copy.copy(dev_agent)
    clone.manifests = ManifestSet([a for a in dev_agent.registry.agents if a["agent_id"] != ROLE_ID])
    with pytest.raises(PermissionError, match="no manifest"):
        GuardReserveAgent(clone, GuardReservePolicy.load())


def test_platform_manifest_and_migration_0021_agree():
    entry = next(a for a in json.loads((ROOT / "backend/app/agents/registry.json").read_text())["agents"]
                 if a["agent_id"] == ROLE_ID)
    assert entry["parent_agent"] == "benefits_intelligence_agent"
    assert entry["may_pull_from_agents"] is False and entry["may_issue_determinations"] is False
    assert entry["writable_data_classes"] == [] and {"V3", "V4", "V5"} <= set(entry["prohibited_data_classes"])
    sql = (ROOT / "database/migrations/0021_guard_reserve_agent.sql").read_text()
    assert f"configuration_hash      = '{sha256_hex(entry)}'" in sql
    for tool in entry["approved_tools"]:
        assert f"'{tool}'" in sql


def test_policy_names_the_parent_and_rejects_drift():
    raw = yaml.safe_load(POLICY_PATH.read_text())
    dataset = json.loads((ROOT / raw["dataset"]).read_text())
    bad = copy.deepcopy(raw)
    bad["parent_agent"] = "guard_reserve_agent"
    with pytest.raises(PolicyError):
        GuardReservePolicy(bad, dataset)
    bad = copy.deepcopy(raw)
    bad["derivation"]["by_duty_status"]["agr32"]["discharge"] = "honorable"       # may derive only service facts
    with pytest.raises(PolicyError):
        GuardReservePolicy(bad, dataset)
    bad = copy.deepcopy(raw)
    del bad["derivation"]["by_duty_status"]["irr"]                                # every status needs a derivation
    with pytest.raises(PolicyError):
        GuardReservePolicy(bad, dataset)
    bad = copy.deepcopy(raw)
    bad["research_gaps"][0]["status"] = "DONE"
    with pytest.raises(PolicyError):
        GuardReservePolicy(bad, dataset)


def test_policy_hashes_are_the_files():
    policy = default_policy()
    assert policy.policy_sha256 == hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
    assert policy.dataset_sha256 == hashlib.sha256((ROOT / "data/reference/guard_reserve.json").read_bytes()).hexdigest()


def test_policy_text_passes_the_language_guard(dev_role):
    texts = list(dev_role.policy.caveats.values()) + list(dev_role.policy.questions.values())
    assert dev_role.parent.language.check_all(texts) == []


# ── answers ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("raw, message", [
    ({"duty_status": "agr32", "gr_component": "usar"}, "National Guard status"),
    ({"duty_status": "sad", "gr_component": "usnr"}, "National Guard status"),
    ({"gr_component": "usar", "order_authorities": ["a11"]}, "only to the National Guard"),
    ({"gr_component": "arng", "order_authorities": ["a10"]}, "Coast Guard"),
    ({"order_authorities": ["a99"]}, "unknown authority"),
    ({"qualifying_days": -1}, "qualifying_days"),
    ({"qualifying_days": True}, "qualifying_days"),
    ({"duty_status": "agr"}, "duty_status"),
    ({"gr_component": "dodciv"}, "gr_component"),          # civilians are not a Guard or Reserve component
    ({"ssn": "x"}, "unknown Guard & Reserve answer"),
])
def test_answers_are_validated_against_sentinel(raw, message):
    with pytest.raises(ProfileError, match=message):
        parse(raw, default_policy())


def test_unknown_authority_is_allowed_and_flagged():
    profile = parse({"gr_component": "usar", "order_authorities": ["unknown", "a3", "a3"]}, default_policy())
    assert profile.order_authorities == ("a3",) and profile.authorities_unknown


# ── derivation and classification ──────────────────────────────────────────
def test_agr_title32_derives_vault_facts_and_classifies(dev_role):
    env = dev_role.match({"guard_reserve": AGR32, "facts": AL, "as_of": AS_OF}, guest(), NOW)
    derived = {d["fact_key"]: d["value"] for d in env["subject"]["facts_derived"]}
    assert derived == {"component": "guard", "service_status": "serving", "on_active_duty_orders": True}
    c = env["classification"]
    assert c["agr"] is True and c["agr_title"] == "32" and c["duty_status"]["selected_reserve"] is True
    assert c["has_post_9_11_authority"] is True
    assert {a["id"]: a["counts_toward_post_9_11_gi_bill"] for a in c["authorities"]} == {"a11": True, "a13": False}
    assert env["determination"] == "none" and env["kind"] == "guard_reserve_match"


def test_an_answer_the_person_gave_wins_and_the_conflict_is_reported(dev_role):
    env = dev_role.match({"guard_reserve": {"gr_component": "usar", "duty_status": "selres"},
                          "facts": {"component": "active"}, "as_of": AS_OF}, guest(), NOW)
    assert env["subject"]["conflicts"] == [{"fact_key": "component", "answered": "active", "derived": "reserve",
                                            "from": "gr_component", "kept": "answered"}]
    assert "component" not in {d["fact_key"] for d in env["subject"]["facts_derived"]}


def test_unsure_status_derives_uncertain_facts(dev_role):
    env = dev_role.match({"guard_reserve": {"gr_component": "usar", "duty_status": "mob", "unsure": ["duty_status"]},
                          "as_of": AS_OF}, guest(), NOW)
    assert all(not d["certain"] for d in env["subject"]["facts_derived"] if d["from"] == "duty_status")


def test_retired_reserve_derives_retired(dev_role):
    env = dev_role.match({"guard_reserve": {"gr_component": "usafr", "duty_status": "retres"}, "as_of": AS_OF},
                         guest(), NOW)
    assert {d["fact_key"]: d["value"] for d in env["subject"]["facts_derived"]}["service_status"] == "retired"
    assert checks(env)["gr.ch1606"]["outcome"] == "DOES_NOT_MEET_ENCODED_RULES"


def test_status_caveats_go_only_on_records_that_read_the_derived_fact(dev_role):
    env = dev_role.match({"guard_reserve": AGR32, "facts": AL, "as_of": AS_OF}, guest(), NOW)
    for item in env["items"]:
        ids = {c["id"] for c in item["guard_reserve"]["role_caveats"]}
        reads_orders = "on_active_duty_orders" in item["guard_reserve"]["uses_derived_facts"]
        assert ("agr_title32" in ids) == reads_orders
    assert any("agr_title32" in {c["id"] for c in i["guard_reserve"]["role_caveats"]} for i in env["items"])


# ── rule-lead checks ───────────────────────────────────────────────────────
@pytest.mark.parametrize("days, outcome, near", [
    (90, "PRELIMINARY_MATCH", False), (400, "PRELIMINARY_MATCH", False),
    (89, "DOES_NOT_MEET_ENCODED_RULES", True), (85, "DOES_NOT_MEET_ENCODED_RULES", True),
    (84, "DOES_NOT_MEET_ENCODED_RULES", False), (None, "NEEDS_INFORMATION", False),
])
def test_post_9_11_lead_threshold(dev_role, days, outcome, near):
    gr = {"gr_component": "usar", "duty_status": "mob", "order_authorities": ["a6"]}
    if days is not None:
        gr["qualifying_days"] = days
    check = checks(dev_role.match({"guard_reserve": gr, "as_of": AS_OF}, guest(), NOW))["gr.ch33"]
    assert check["outcome"] == outcome
    assert ("near_threshold" in {c["id"] for c in check["caveats"]}) == near


def test_days_without_a_qualifying_authority_go_to_a_person(dev_role):
    gr = {"gr_component": "arng", "duty_status": "selres", "order_authorities": ["a13", "a14"], "qualifying_days": 200}
    assert checks(dev_role.match({"guard_reserve": gr, "as_of": AS_OF}, guest(), NOW))["gr.ch33"]["outcome"] == \
        "HUMAN_REVIEW_REQUIRED"


def test_tier_caveat_for_12304b(dev_role):
    gr = {"gr_component": "usar", "duty_status": "mob", "order_authorities": ["a9"], "qualifying_days": 120}
    check = checks(dev_role.match({"guard_reserve": gr, "as_of": AS_OF}, guest(), NOW))["gr.ch33"]
    assert "tier_caveat" in {c["id"] for c in check["caveats"]}


@pytest.mark.parametrize("status, outcome", [
    ("selres", "PRELIMINARY_MATCH"), ("agr10", "PRELIMINARY_MATCH"),
    ("irr", "DOES_NOT_MEET_ENCODED_RULES"), ("retres", "DOES_NOT_MEET_ENCODED_RULES"),
])
def test_selected_reserve_leads(dev_role, status, outcome):
    env = dev_role.match({"guard_reserve": {"gr_component": "usar", "duty_status": status}, "as_of": AS_OF},
                         guest(), NOW)
    assert checks(env)["gr.ch1606"]["outcome"] == outcome
    assert checks(env)["gr.fta"]["outcome"] == outcome


def test_production_never_shows_an_unreviewed_lead_as_a_match(prod_role):
    env = prod_role.match({"guard_reserve": AGR32, "facts": AL, "as_of": AS_OF}, guest(), NOW)
    assert checks(env)["gr.ch33"]["outcome"] == "HUMAN_REVIEW_REQUIRED"
    assert "RECORD_NOT_VERIFIED" in checks(env)["gr.ch33"]["reasons"]
    assert env["counts"]["PRELIMINARY_MATCH"] == 0


def test_contested_lead_and_state_definition_notice(dev_role):
    env = dev_role.match({"guard_reserve": {"gr_component": "arng", "duty_status": "selres"}, "facts": AL,
                          "as_of": AS_OF}, guest(), NOW)
    assert checks(env)["gr.rudisill"]["outcome"] == "CONFLICTING_AUTHORITY"
    notice = checks(env)["gr.state_definition_trap"]
    assert notice["kind"] == "notice" and notice["applies"] is True
    later = dev_role.match({"guard_reserve": {"gr_component": "arng", "duty_status": "selres"},
                            "facts": {**AL, "active_duty_days": 400}, "as_of": AS_OF}, guest(), NOW)
    assert checks(later)["gr.state_definition_trap"]["applies"] is False
    assert "gr.naturalization" not in checks(env)                    # needs facts VetBuddy never collects


def test_every_outcome_is_a_v6_outcome(dev_role):
    for status in dev_role.policy.statuses:
        comp = "arng"
        env = dev_role.match({"guard_reserve": {"gr_component": comp, "duty_status": status}, "as_of": AS_OF},
                             guest(), NOW)
        assert {i["outcome"] for i in env["items"]} <= set(OUTCOMES)
        assert {c["outcome"] for c in env["rule_lead_checks"] if c["kind"] == "rule_lead_check"} <= set(OUTCOMES)


# ── the lens ───────────────────────────────────────────────────────────────
def test_lens_puts_guard_reserve_records_first_and_hides_nothing(dev_role, dev_agent):
    request = {"guard_reserve": AGR32, "facts": AL, "as_of": AS_OF}
    env = dev_role.match(request, guest(), NOW)
    sections = [i["guard_reserve"]["section"] for i in env["items"]]
    assert sections == sorted(sections, key=lambda s: s != "guard_reserve")
    plain = dev_agent.match({"facts": {**AL, "component": "guard", "service_status": "serving",
                                       "on_active_duty_orders": True}, "as_of": AS_OF}, guest(), NOW)
    assert {i["benefit_id"] for i in env["items"]} == {i["benefit_id"] for i in plain["items"]}
    assert env["counts"] == plain["counts"]
    only = dev_role.match({**request, "include_other": False}, guest(), NOW)
    assert {i["guard_reserve"]["section"] for i in only["items"]} == {"guard_reserve"}
    assert only["section_counts"] == env["section_counts"]


def test_selection_covers_guard_categories_and_tokens(dev_role, registry):
    for benefit in registry.benefits.values():
        if benefit.category in ("GUARD_EDU", "GUARD_PAY") or "gr.ch33" in benefit.lead_ids:
            assert dev_role.is_guard_reserve(benefit)
    counts = dev_role.selection_counts()
    assert counts["records"] == counts["federal"] + counts["state_and_territory"] > 300


def test_envelope_is_deterministic_and_answers_are_not_echoed_elsewhere(dev_role):
    request = {"guard_reserve": AGR32, "facts": AL, "as_of": AS_OF}
    a = dev_role.match(request, guest("one"), NOW)
    b = dev_role.match(request, guest("two"), NOW)
    assert a["hashes"] == b["hashes"]
    c = dev_role.match({**request, "guard_reserve": {**AGR32, "qualifying_days": 89}}, guest(), NOW)
    assert c["hashes"]["inputs"] != a["hashes"]["inputs"]


def test_guest_mode_drops_v2_facts(dev_role):
    env = dev_role.match({"guard_reserve": AGR32, "facts": {**AL, "va_rating": 30}, "as_of": AS_OF}, guest(), NOW)
    assert env["subject"]["facts_not_used_in_this_mode"] == ["va_rating"]


def test_crisis_and_mst_screens_run_first(dev_role):
    env = dev_role.match({"guard_reserve": {"duty_status": "nonsense"}, "note": "I want to kill myself"},
                         guest(), NOW)
    assert env["kind"] == "crisis_floor"


def test_bad_answers_are_a_request_error(dev_role):
    with pytest.raises(RequestError):
        dev_role.match({"guard_reserve": {"duty_status": "agr32", "gr_component": "usar"}}, guest(), NOW)
    with pytest.raises(RequestError):
        dev_role.match({"guard_reserve": AGR32, "include_other": "yes"}, guest(), NOW)


def test_missing_answers_become_questions(dev_role):
    env = dev_role.match({"facts": AL, "as_of": AS_OF}, guest(), NOW)
    asked = {q["fact_key"] for q in env["questions"]}
    assert {"gr_component", "duty_status"} <= asked
    assert "authority_from_orders" in {c["id"] for c in env["general_caveats"]}


# ── pulls go through the parent, never the role ────────────────────────────
class Provider:
    def __init__(self, values):
        self.values, self.calls = values, []

    def provide(self, tenant_ref, keys):
        self.calls.append(sorted(keys))
        return {k: v for k, v in self.values.items() if k in keys}


def test_pulls_run_through_benefits_intelligence_for_only_what_is_still_needed(registry):
    provider = Provider({"guard_state": "TX", "component": "reserve", "service_status": "retired"})
    parent = BenefitVaultAgent(registry, providers={"service_profile_agent": provider}, environment="development")
    role = GuardReserveAgent(parent)
    session = Session(mode="B", tenant_ref=TENANT_A)
    parent.create_grant({"source_agent": "service_profile_agent", "confirm": True,
                         "fact_keys": ["guard_state", "component", "service_status"]}, session, NOW)
    env = role.match({"guard_reserve": {"gr_component": "arng", "duty_status": "selres"},
                      "facts": {"residence_state": "TX"}, "as_of": AS_OF}, session, NOW + timedelta(minutes=1))
    # Component and status came from the person's own answers, so only the Guard state was pulled.
    assert provider.calls == [["guard_state"]]
    assert {p["fact_key"] for p in env["subject"]["facts_pulled"]} == {"guard_state"}
    entries = parent.ledger(session)["entries"]
    assert [e["event"] for e in entries] == ["GRANT_CREATED", "PULL_ALLOWED"]
    assert {e["requester"] for e in entries} == {"benefits_intelligence_agent"}


# ── routes ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def client(dev_role):
    return TestClient(Starlette(routes=gr_api.routes(dev_role, clock=lambda: NOW)))


def test_routes(client):
    cat = client.get(f"{gr_api.PREFIX}/catalog").json()
    assert cat["role"]["role_id"] == ROLE_ID and cat["manifest"]["may_pull_from_agents"] is False
    assert {s["id"] for s in cat["duty_statuses"]} >= {"agr32", "agr10", "selres", "tech", "mob", "sad"}
    assert {g["status"] for g in cat["research_gaps"]} <= {"IMPLEMENTED_UNVERIFIED", "PARTIAL", "SOURCE_NOT_AVAILABLE"}
    leads = client.get(f"{gr_api.PREFIX}/leads").json()
    assert all(l["lead_id"].startswith("gr.") for l in leads["rule_leads"])
    ok = client.post(f"{gr_api.PREFIX}/match", json={"guard_reserve": AGR32, "facts": AL, "as_of": AS_OF})
    assert ok.status_code == 200 and ok.json()["mode"] == "A"
    bad = client.post(f"{gr_api.PREFIX}/match", json={"guard_reserve": {"duty_status": "x"}})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "VALIDATION_FAILED"


def test_routes_are_mounted_in_the_app():
    text = (ROOT / "backend/app/api/v1.py").read_text()
    assert "guard_reserve_api.routes(role" in text


# ── recovered Gemini leads (ADR 0011 addendum) ─────────────────────────────
import subprocess  # noqa: E402

from app.domains.vault.guard_reserve.recovered import RecoveredLeads  # noqa: E402

GEMINI = ROOT / "data/research/recovered/gemini_guard_reserve"


def test_extraction_is_current_and_every_file_matches_the_manifest():
    res = subprocess.run(["python3", str(ROOT / "scripts/extract_gemini_guard_reserve.py"), "--check"],
                         capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr
    manifest = json.loads((ROOT / "data/research/recovered/RECOVERY_MANIFEST.json").read_text())
    entries = {e["path"]: e for e in manifest["entries"] if e["path"].startswith("gemini_guard_reserve/")}
    assert set(entries) == {"gemini_guard_reserve/report.html", "gemini_guard_reserve/jurisdictions_56.json",
                            "gemini_guard_reserve/federal_leads.json"}
    for path, entry in entries.items():
        data = (ROOT / "data/research/recovered" / path).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"] and entry["tier"] == 4


def test_registry_lists_the_recovered_datasets(registry):
    paths = {d["path"] for d in registry.data["recovered_datasets"]}
    assert {"gemini_guard_reserve/jurisdictions_56.json", "gemini_guard_reserve/federal_leads.json"} <= paths


def test_a_tampered_recovered_file_is_refused(tmp_path):
    import shutil
    src = ROOT / "data/research/recovered"
    shutil.copy(src / "RECOVERY_MANIFEST.json", tmp_path / "RECOVERY_MANIFEST.json")
    (tmp_path / "gemini_guard_reserve").mkdir()
    for name in ("jurisdictions_56.json", "federal_leads.json"):
        shutil.copy(src / "gemini_guard_reserve" / name, tmp_path / "gemini_guard_reserve" / name)
    RecoveredLeads(default_policy(), tmp_path)                                    # untouched: loads
    path = tmp_path / "gemini_guard_reserve/federal_leads.json"
    path.write_text(path.read_text().replace("$645.90", "$64.59"))
    with pytest.raises(PolicyError, match="hash"):
        RecoveredLeads(default_policy(), tmp_path)


def test_report_table_has_56_jurisdictions_and_its_own_count_is_checked():
    data = json.loads((GEMINI / "jurisdictions_56.json").read_text())
    codes = {r["code"] for r in data["jurisdictions"]}
    assert len(codes) == 56 and {"PR", "VI", "GU", "AS", "MP", "DC"} <= codes
    tuition = next(c for c in data["report_consistency"] if "tuition" in c["claim"])
    assert tuition["table_count"] == 52 and tuition["agrees"] is False          # the report says 51
    assert next(c for c in data["report_consistency"] if "income tax" in c["claim"])["agrees"] is True
    rows = {r["code"]: r for r in data["jurisdictions"]}
    assert "title_10_32_split" in rows["IA"]["tags"] and "agr_specific_rule" in rows["UT"]["tags"]
    assert "no_national_guard" in rows["AS"]["tags"] and "no_national_guard" in rows["MP"]["tags"]
    assert rows["CT"]["cross_check"]["relation"] == "not_in_vault"
    assert rows["NM"]["cross_check"]["relation"] == "report_lists_none_vault_has_record"


def test_recovered_leads_are_leads_never_outcomes(dev_role):
    env = dev_role.match({"guard_reserve": AGR32, "facts": {"residence_state": "MO", "guard_state": "IA"},
                          "as_of": AS_OF}, guest(), NOW)
    rec = env["recovered_leads"]
    assert [j["code"] for j in rec["jurisdictions"]] == ["IA", "MO"]            # Guard state first
    for lead in rec["jurisdictions"] + rec["federal"]:
        assert "outcome" not in lead and lead["record_status"] == "UNVERIFIED" and lead["tier"] == 4
        assert lead["caveats"][0]["id"] == "recovered_ai_lead"
        assert lead["check_state"] in ("NOT_OPENED", "CHECKED", "CORRECTED")
        assert lead["source_opened"] == bool(lead["source_checks"]) or lead["check_state"] == "NOT_OPENED"
    assert {f["lead_id"] for f in rec["federal"]} >= {"GF12"}                    # AGR retirement
    assert "GF05" not in {f["lead_id"] for f in rec["federal"]}                  # Gray Area is not an AGR lead


def test_a_cell_the_language_guard_flags_is_withheld_not_reworded(dev_role):
    row = dev_role.recovered.jurisdiction("MO")
    assert row["other"] is None and row["withheld_by_language_guard"] == ["other"]
    assert row["named_source"].startswith("https://myarmybenefits.us.army.mil/")
    whole = dev_role.recovered_leads(guest())
    assert len(whole["jurisdictions"]) == 56 and whole["determination"] == "none"


def test_federal_lead_texts_pass_the_language_guard_and_name_known_gaps(dev_role):
    texts = [l["claim"] for l in dev_role.recovered.federal] + [l.get("review_note") or "" for l in
                                                               dev_role.recovered.federal]
    assert dev_role.parent.language.check_all(texts) == []
    gaps = {g["id"] for g in dev_role.policy.research_gaps}
    assert all(set(l["gap_ids"]) <= gaps for l in dev_role.recovered.federal)


def test_recovered_routes(client):
    one = client.get(f"{gr_api.PREFIX}/recovered/tx").json()
    assert one["jurisdictions"][0]["code"] == "TX" and one["kind"] == "guard_reserve_recovered"
    assert client.get(f"{gr_api.PREFIX}/recovered/zz").status_code == 422
    cat = client.get(f"{gr_api.PREFIX}/catalog").json()
    assert cat["recovered"]["jurisdiction_rows"] == 56 and cat["recovered"]["federal_leads"] == 15


def test_source_queue_puts_agr_and_gray_area_first_and_lists_every_source_once(dev_role):
    env = dev_role.source_queue(guest())
    queue = env["queue"]
    urls = [q["url"] for q in queue]
    assert len(urls) == len(set(urls)) and env["executable"] is False
    assert queue[0]["cited_by"] == ["GF12"]                                       # AGR retirement first
    assert {q["state"] for q in queue} <= {"OPENED", "FETCH_FAILED", "NOT_OPENED"}
    named = {u for l in dev_role.recovered.federal for u in l["named_sources"]}
    named |= {r["named_source"] for r in dev_role.recovered.jurisdictions.values()}
    assert set(urls) == named
    first_state = next(i for i, q in enumerate(queue) if q["cited_by"][0].startswith("GJ."))
    agr_states = {c for c, r in dev_role.recovered.jurisdictions.items() if "agr_specific_rule" in r["tags"]}
    assert {q["cited_by"][0][3:] for q in queue[first_state:first_state + len(agr_states)]} == agr_states


def test_source_queue_route(client):
    r = client.get(f"{gr_api.PREFIX}/source-queue").json()
    assert r["kind"] == "guard_reserve_source_queue" and r["counts"]["sources"] == len(r["queue"])


# ── source checks of 2026-11-21 ────────────────────────────────────────────
CHECKS = ROOT / "data/research/guard_reserve/source_checks.json"


def test_every_opened_source_wrote_only_records_from_its_own_page(registry):
    doc = json.loads(CHECKS.read_text())
    for check in doc["checks"]:
        for rid in check["records"]:
            assert registry.benefits[rid].record_status in ("SOURCE_CHECKED", "UNVERIFIED")      # never VERIFIED (G1)
    failed = [c for c in doc["checks"] if c["result"] == "fetch_failed"]
    assert failed and all(not c["findings"] and not c["records"] for c in failed)


def test_new_guard_reserve_records_are_in_the_registry_with_their_rules(registry):
    expect = {
        "us.tricare-retired-reserve": "(ret & age<60) | (dep & spret)",
        "us.tricare-prime-and-select-at-age-60-for-retired-guard-and-reserve-members": "(ret & age>=60) | (dep & spret)",
        "us.reduced-retirement-age-for-qualifying-active-duty": "ngany | rsv",
        "us.concurrent-retirement-and-disability-pay-crdp": "ret & r>=50",
        "us.combat-related-special-compensation-crsc": "ret & r>=10",
    }
    for rid, rule in expect.items():
        assert registry.benefits[rid].rule == rule


def test_crdp_correction_is_shown_on_the_gemini_lead(dev_role):
    lead = next(l for l in dev_role.recovered.federal_for(None) if l["lead_id"] == "GF13")
    assert lead["check_state"] == "CORRECTED"
    assert any(f["verdict"] == "DIFFERS" and "50%" in f["note"] for f in lead["source_checks"])
    assert "us.concurrent-retirement-and-disability-pay-crdp" in lead["records"]


def test_reduced_age_check_records_what_the_report_left_out(dev_role):
    lead = next(l for l in dev_role.recovered.federal_for(None) if l["lead_id"] == "GF06")
    note = lead["source_checks"][0]["note"]
    assert lead["source_checks"][0]["verdict"] == "AGREES_IN_PART" and "two consecutive fiscal years" in note


def test_gap_records_exist_and_retired_reserve_now_matches(dev_role):
    gaps = {g["id"]: g for g in dev_role.policy.research_gaps}
    assert gaps["GRG01"]["status"] == "IMPLEMENTED_UNVERIFIED"
    assert gaps["GRG13"]["status"] == "PARTIAL"                                  # Iowa and Utah AGR tax still open
    env = dev_role.match({"guard_reserve": {"gr_component": "usar", "duty_status": "retres"},
                          "facts": {"age": 52}, "as_of": AS_OF}, guest(), NOW)
    found = {i["benefit_id"]: i for i in env["items"]}
    assert found["us.tricare-retired-reserve"]["outcome"] == "PRELIMINARY_MATCH"
    assert found["us.tricare-retired-reserve"]["guard_reserve"]["section"] == "guard_reserve"


def test_source_queue_reports_opened_pages(dev_role):
    counts = dev_role.source_queue(guest())["counts"]
    assert counts["opened"] == 81 and counts["fetch_failed"] == 2 and counts["not_opened"] == 0
    assert counts["opened"] + counts["fetch_failed"] + counts["not_opened"] == counts["sources"]


def test_check_notes_pass_the_language_guard(dev_role):
    notes = [f["note"] for found in dev_role.recovered.checks_by_lead.values() for f in found]
    assert dev_role.parent.language.check_all(notes) == []


def test_agr_member_now_sees_agr_retirement_and_health_care(dev_role):
    env = dev_role.match({"guard_reserve": {"gr_component": "arng", "duty_status": "agr32"}, "as_of": AS_OF},
                         guest(), NOW)
    found = {i["benefit_id"]: i for i in env["items"]}
    for rid in ("us.army-agr-retirement-after-20-years-of-active-federal-service",
                "us.blended-retirement-system-retired-pay-for-army-guard-agr-and-full-time-n",
                "us.tricare-prime-for-guard-members-on-federal-active-duty-including-full-ti"):
        assert found[rid]["outcome"] == "PRELIMINARY_MATCH"
        assert found[rid]["guard_reserve"]["section"] == "guard_reserve"
        assert "agr_title32" in {c["id"] for c in found[rid]["guard_reserve"]["role_caveats"]}
    gaps = {g["id"]: g for g in dev_role.policy.research_gaps}
    assert gaps["GRG03"]["status"] == gaps["GRG04"]["status"] == "IMPLEMENTED_UNVERIFIED"


def test_pages_found_by_search_are_marked_as_not_named_by_the_report():
    doc = json.loads(CHECKS.read_text())
    extra = [c for c in doc["checks"] if c.get("named_by_report") is False]
    assert len(extra) == 3 and all(c["records"] for c in extra)


def test_every_named_jurisdiction_page_was_checked(dev_role):
    for code, row in dev_role.recovered.jurisdictions.items():
        lead = dev_role.recovered.jurisdiction(code)
        assert lead["check_state"] in ("CHECKED", "CORRECTED"), code
        assert lead["source_opened"] is True


def test_line_of_duty_record_closes_its_gap(dev_role):
    gaps = {g["id"]: g for g in dev_role.policy.research_gaps}
    assert gaps["GRG08"]["status"] == "IMPLEMENTED_UNVERIFIED"
    lead = next(l for l in dev_role.recovered.federal_for(None) if l["lead_id"] == "GF03")
    assert "us.line-of-duty-determination-for-army-guard-and-reserve-injuries-and-illne" in lead["records"]
