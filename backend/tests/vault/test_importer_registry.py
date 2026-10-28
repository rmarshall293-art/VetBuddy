"""The ledger importer, the registry build and the registry's pins."""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from app.domains.vault.canonical import canonical_json, sha256_hex
from app.domains.vault.discovery import importer
from app.domains.vault.guards import LanguageGuard
from app.domains.vault.registry import DEFAULT_PATH, RegistryError, Review, VaultRegistry
from app.domains.vault import vocab
from app.domains.vault.facts import CATALOG, FactSet, resolver, within_ceiling
from app.domains.vault.rules import evaluate, tokens
from app.domains.vault.tri import Tri
from app.domains.vault.vocab import JURISDICTIONS, OUTCOMES

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def raw():
    return json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))


def restamp(data):
    body = {k: v for k, v in data.items() if k != "integrity"}
    data["integrity"]["sha256"] = sha256_hex(canonical_json(body))
    return data


# ── importer ──────────────────────────────────────────────────────────────

def test_split_row_keeps_or_inside_the_rule():
    row = "PARKS|Pass|vet,dv|res & (vet | ss) | gs|Who|Value|https://example.gov/a"
    assert importer.split_row(row) == ("PARKS", "Pass", "vet,dv", "res & (vet | ss) | gs", "Who", "Value",
                                       "https://example.gov/a")
    with pytest.raises(ValueError):
        importer.split_row("A|B|C|D|E|F")


def test_tiers_by_host():
    assert importer.tier_for("https://www.va.gov/x") == 1
    assert importer.tier_for("https://dot.state.wy.us/x") == 1
    assert importer.tier_for("https://myarmybenefits.us.army.mil/x") == 2
    assert importer.tier_for("https://law.justia.com/x") == 2
    assert importer.tier_for("https://www.fisherhouse.org/x") == 3
    assert importer.tier_for(None) == 4


def write_ledger(tmp_path: Path, body: str, name="states/test.psv") -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


HEADER = "# JUR=TX SRC=https://myarmybenefits.us.army.mil/Benefit-Library/State/Territory-Benefits/Texas PAGE_UPDATED=none\n"


def build_one(tmp_path, body, name="states/test.psv"):
    path = write_ledger(tmp_path, body, name)
    ledger = importer.parse_ledger(path, tmp_path)
    return importer.build([ledger], "2026-10-27")


def test_import_one_row(tmp_path):
    sources, benefits, tails = build_one(tmp_path, HEADER + "PARKS|Free pass|vet|res & vet|Texas veterans|Free entry|PAGE\n")
    assert len(sources) == 1 and sources[0]["page_status"] == "OPENED" and sources[0]["tier"] == 2
    item = benefits[0]
    assert item["benefit_id"] == "tx.free-pass"
    assert item["official_url"] == sources[0]["url"] and item["official_url_status"] == "SAME_AS_SOURCE"
    assert item["record_status"] == "UNVERIFIED" and item["kind"] == "STATE_BENEFIT"
    assert item["content_hash"] == sha256_hex({k: item[k] for k in (
        "jurisdiction", "category", "title", "groups", "rule", "who_it_is_for", "value", "official_url")})
    assert tails == []


@pytest.mark.parametrize("row,message", [
    ("PASS|X|vet|res|W|V|PAGE", "federal-only"),
    ("NOPE|X|vet|res|W|V|PAGE", "unknown category"),
    ("PARKS|X|vets|res|W|V|PAGE", "unknown group"),
    ("PARKS|X|vet,vet|res|W|V|PAGE", "listed twice"),
    ("PARKS|X|vet|res &|W|V|PAGE", "rule ends early"),
    ("PARKS|X|vet|res|W|V|http://insecure.gov", "https"),
    ("PARKS||vet|res|W|V|PAGE", "TITLE is empty"),
])
def test_bad_rows_are_refused(tmp_path, row, message):
    with pytest.raises(importer.LedgerError) as info:
        build_one(tmp_path, HEADER + row + "\n")
    assert message in str(info.value)


def test_row_before_header_and_bad_header(tmp_path):
    with pytest.raises(importer.LedgerError):
        build_one(tmp_path, "PARKS|X|vet|res|W|V|PAGE\n")
    with pytest.raises(importer.LedgerError):
        build_one(tmp_path, "# JUR=ZZ SRC=https://x.gov PAGE_UPDATED=none\n")
    with pytest.raises(importer.LedgerError):
        build_one(tmp_path, "# JUR=US SRC=none\nPASS|X|vet|vet|W|V|https://x.org\n", "federal/f.psv")


def test_seen_in_search_rows_are_tier_four_leads(tmp_path):
    body = "# JUR=US SRC=none SEEN_IN_SEARCH=2026-10-27\nTICKETS|Offer|vet|vet|Who|What|https://deals.example.com/\n"
    sources, benefits, _ = build_one(tmp_path, body, "federal/f.psv")
    assert sources[0]["page_status"] == "SEEN_IN_SEARCH" and sources[0]["tier"] == 4
    assert benefits[0]["official_url_status"] == "SEEN_IN_SEARCH" and benefits[0]["record_status"] == "UNVERIFIED"
    with pytest.raises(importer.LedgerError):
        build_one(tmp_path, "# JUR=US SRC=none SEEN_IN_SEARCH=2026-10-27\nTICKETS|Offer|vet|vet|W|V|PAGE\n",
                  "federal/g.psv")


def test_duplicate_titles_get_a_suffix(tmp_path):
    body = HEADER + "PARKS|Pass|vet|vet|W|V|PAGE\nPARKS|Pass|vet|vet|W2|V2|PAGE\n"
    _, benefits, _ = build_one(tmp_path, body)
    assert [b["benefit_id"] for b in benefits] == ["tx.pass", "tx.pass-2"]


def test_full_ledgers(registry):
    counts = registry.data["counts"]
    assert counts["benefits"] == len(registry.benefits) == 1362
    assert counts["by_kind"] == {"COMMERCIAL_DEAL": 9, "FEDERAL_BENEFIT": 60, "NONPROFIT_PROGRAM": 12, "STATE_BENEFIT": 1281}
    assert counts["verified"] == 0
    covered = {c for c, j in registry.jurisdictions.items() if j["coverage"] == "COVERED"}
    assert covered == set(JURISDICTIONS) - {"AS"}
    assert registry.jurisdictions["AS"]["coverage"] == "SOURCE_NOT_AVAILABLE"
    by_jur = Counter(b.jurisdiction for b in registry.benefits.values())
    assert all(by_jur[c] >= 5 for c in covered)
    seen = [b for b in registry.benefits.values() if b.official_url_status == "SEEN_IN_SEARCH"]
    assert len(seen) == 6 and all(b.source_tier == 4 and b.record_status == "UNVERIFIED" for b in seen)


# Family-tagged records whose rule is about the member alone, on purpose:
# Guard and Reserve programs whose family coverage runs through the member's
# own enrollment (rule tokens only ng, ngany, rsv), and records whose family
# tag is broader than the text read (defect register VD11).
TAG_BROADER_THAN_TEXT = {
    ("ar.disabled-veteran-license-plate", "ss"), ("de.delaware-veterans-home-milford", "ss"),
    ("ga.disabled-veteran-license-plate", "ss"), ("ne.veteran-homestead-exemption-wartime", "ss"),
    ("nh.new-hampshire-veterans-home-tilton", "sp"), ("tn.tennessee-state-veterans-homes", "sp"),
    ("sd.burial-allowance-and-headstone-setting-fee", "sp"), ("tn.state-sponsored-life-insurance", "ss"),
    # A spouse of a member killed on duty is a surviving spouse (ss), which these rules include.
    ("in.grant-for-children-and-spouse-of-guard-members-killed-on-state-duty", "sp"),
    ("ma.military-family-relief-fund", "sp"),
}


def _family_profiles(group, jurisdiction):
    """Family members with the strongest sponsor facts, living in or out of the record's state."""
    sponsor = {"sponsor_service_connected": True, "sponsor_va_rating": 100, "sponsor_permanent_total": True,
               "sponsor_unemployability": True, "service_status": "never_served"}
    for home in ([jurisdiction, "OK" if jurisdiction == "TX" else "TX"] if jurisdiction != "US" else ["TX"]):
        station = {"duty_station_state": home if jurisdiction == "US" else jurisdiction}
        if group in ("sp", "ch"):
            relationship = "spouse" if group == "sp" else "child"
            for status in ("serving", "separated", "retired") + (("deceased",) if group == "ch" else ()):
                for mia in (False, True):
                    for age in ((30, 65) if group == "sp" else (8, 15, 20)):
                        yield {**sponsor, **(station if status == "serving" else {}), "residence_state": home,
                               "relationship": relationship, "sponsor_status": status, "sponsor_pow_mia": mia,
                               "sponsor_died_in_line_of_duty": status == "deceased",
                               "gold_star_family": status == "deceased", "age": age}
        else:
            relationships = ("surviving_spouse",) if group == "ss" else ("parent", "surviving_spouse", "child")
            for relationship in relationships:
                for killed in (False, True) if group == "ss" else (True,):
                    for age in (40, 65) if relationship != "child" else (17,):
                        yield {**sponsor, "residence_state": home, "relationship": relationship,
                               "sponsor_status": "deceased", "sponsor_pow_mia": False,
                               "sponsor_died_in_line_of_duty": killed, "gold_star_family": killed, "age": age}


def test_family_tagged_records_can_match_a_family_member(registry):
    member_only = {"ng", "ngany", "rsv", "res"}
    unmatched = set()
    for benefit in registry.benefits.values():
        for group in ("sp", "ss", "ch", "gs"):
            if group not in benefit.groups:
                continue
            if any(evaluate(benefit.node, resolver(FactSet.from_mapping(f), benefit.jurisdiction))[0] is not Tri.FALSE
                   for f in _family_profiles(group, benefit.jurisdiction)):
                continue
            if {t.name for t in tokens(benefit.node)} <= member_only:
                continue
            unmatched.add((benefit.benefit_id, group))
    assert unmatched == TAG_BROADER_THAN_TEXT


def test_every_state_tail_was_read_or_marked(registry):
    """Pages longer than one read either have a tail block or say how much is unread."""
    tails = {t["jurisdiction"] for t in registry.data["tail_reads"]}
    assert {"LA", "MA", "NY", "TX", "WA", "CA", "FL"} <= tails
    assert registry.jurisdictions["NM"]["tail_unread_chars"] == 451


def test_build_is_deterministic_and_current():
    for script in ("build_vault_registry.py", "build_vault_seed.py"):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / script), "--check"],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_registry_texts_pass_the_language_guard(registry):
    guard = LanguageGuard()
    texts = [registry.notice] + list(registry.caveats.values())
    for benefit in registry.benefits.values():
        texts += [benefit.title, benefit.who_it_is_for, benefit.value]
    assert guard.check_all(texts) == []


def test_registry_matches_the_policy_file(registry):
    import yaml

    policy = yaml.safe_load((ROOT / "config" / "benefit_vault_policy.yaml").read_text(encoding="utf-8"))
    assert registry.version == policy["version"] and registry.as_of == policy["as_of"]
    # The notice is the v6 common notice from the one governance language file (C-09, VD15).
    language = yaml.safe_load((ROOT / "config" / "governance_language.yaml").read_text(encoding="utf-8"))
    assert policy["notice_from"] == "governance_language.common_notice" and "notice" not in policy
    assert registry.notice == " ".join(language["common_notice"].split())
    assert [a["agent_id"] for a in registry.agents] == sorted(a["agent_id"] for a in policy["agents"])
    assert registry.governance["publish_policy"] == policy["publish_policy"]


def _sql_lists(text, pattern):
    """The quoted values of each bracketed list that follows a regex anchor in the migration."""
    out = []
    for match in re.finditer(pattern, text):
        depth, end = 1, match.end()
        while depth:
            depth += text[end] in "(["
            depth -= text[end] in ")]"
            end += 1
        out.append(re.findall(r"'([^']*)'", text[match.end():end - 1]))
    assert out, pattern
    return out


def test_sql_checks_name_exactly_the_vocabulary():
    text = (ROOT / "database" / "migrations" / "0014_benefit_vault.sql").read_text(encoding="utf-8")
    statuses_without_verified = [s for s in vocab.RECORD_STATUSES if s != "VERIFIED"]
    mode_b = [c for c in vocab.DATA_CLASSES if within_ceiling(c, "B")]
    expected = {
        r"CHECK \(page_status IN \(": [list(vocab.PAGE_STATUSES)],
        r"CHECK \(data_class IN \(": [list(vocab.DATA_CLASSES), mode_b],
        r"CHECK \(category IN \(": [list(vocab.CATEGORIES)],
        r"kind = 'STATE_BENEFIT' AND category IN \(": [list(vocab.STATE_CATEGORIES)],
        r"groups <@ ARRAY\[": [list(vocab.GROUPS)],
        r"CHECK \(official_url_status IN \(": [list(vocab.URL_STATUSES)],
        r"CHECK \(record_status IN\s*\(": [list(vocab.RECORD_STATUSES), statuses_without_verified],
        r"CHECK \(highest_class_held IN \(": [list(vocab.DATA_CLASSES)],
        r"CHECK \(event IN \(": [list(vocab.VAULT_EVENTS)],
        r"CHECK \(reason IN \(": [[vocab.ALLOW_REASON, *vocab.DENIAL_REASONS]],
        r"CHECK \(status IN \(": [list(vocab.SAVED_STATUSES)],
        r"IF c NOT IN \(": [mode_b],
    }
    for pattern, lists in expected.items():
        assert _sql_lists(text, pattern) == lists, pattern
    kinds = _sql_lists(text, r"CHECK \(kind IN \(")
    assert kinds[1] == list(vocab.KINDS)
    assert {spec.kind for spec in CATALOG.values()} <= set(kinds[0])
    assert re.findall(r"CHECK \(purpose = '([a-z_]+)'\)", text) == list(vocab.PULL_PURPOSES)
    assert f"verified_by ~ '{vocab.REVIEWER_HANDLE}'" in text


def test_recovered_data_is_hash_checked(registry):
    datasets = {d["path"]: d for d in registry.data["recovered_datasets"]}
    for path in ("zip_guard_reserve/license_reciprocity_51.json", "zip_recreation/recreation_seed_10.json",
                 "zip_recreation/demo_recreation_13.json", "slice02/guard_reserve.json"):
        assert datasets[path]["location"] is not None
        assert sha256_hex((ROOT / datasets[path]["location"]).read_bytes()) == datasets[path]["sha256"]
    # The slice 02 governance files ship as provenance copies (hash-checked); the
    # runtime files in config/ moved on in slice 03 (ADR 0005).
    for config in ("slice02/crisis_floor.yaml", "slice02/governance_language.yaml"):
        location = datasets[config]["location"]
        assert location == f"data/research/recovered/{config}"
        assert sha256_hex((ROOT / location).read_bytes()) == datasets[config]["sha256"]
    leads = {lead["lead_id"]: lead for lead in registry.recovered_leads}
    assert len(leads) == 23 and leads["RB12"]["cross_check"]["relation"] == "differs"
    assert all(lead["tier"] == 4 for lead in leads.values())
    assert registry.rule_leads["gr.n426_180_day"]["record_status"] == "SUPERSEDED"


# ── registry pins ─────────────────────────────────────────────────────────

def test_integrity_stamp_detects_tampering(raw):
    data = copy.deepcopy(raw)
    data["benefits"][0]["value"] = "changed"
    with pytest.raises(RegistryError, match="integrity"):
        VaultRegistry(data, check_schema=False)


def test_content_hash_detects_edits_even_when_restamped(raw):
    data = copy.deepcopy(raw)
    data["benefits"][0]["value"] = "changed"
    with pytest.raises(RegistryError, match="content hash"):
        VaultRegistry(restamp(data), check_schema=False)


def _agent(data, agent_id):
    return next(a for a in data["governance"]["agents"] if a["agent_id"] == agent_id)


@pytest.mark.parametrize("mutate,match", [
    (lambda d: _agent(d, "household_agent").update(may_issue_determinations=True), "determinations"),
    (lambda d: _agent(d, "household_agent").update(may_pull_from_agents=True), "pull"),
    (lambda d: _agent(d, "benefit_vault_agent").update(may_pull_from_agents=False), "pull"),
    (lambda d: _agent(d, "va_status_agent")["exposes"].append({"fact_key": "severe_disability", "data_class": "V4"}),
     "expose"),
    (lambda d: _agent(d, "service_profile_agent")["exposes"][0].update(data_class="V1" if
     _agent(d, "service_profile_agent")["exposes"][0]["data_class"] == "V2" else "V2"), "expose"),
])
def test_manifest_pins_in_the_loader(raw, mutate, match):
    data = copy.deepcopy(raw)
    mutate(data)
    with pytest.raises(RegistryError, match=match):
        VaultRegistry(restamp(data), check_schema=False)


def test_manifest_pins_in_the_schema(raw):
    import jsonschema

    schema = json.loads((ROOT / "schemas" / "json" / "benefit_vault_registry.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(schema)
    assert not list(validator.iter_errors(raw))
    for mutate in (lambda d: _agent(d, "household_agent").update(may_issue_determinations=True),
                   lambda d: _agent(d, "household_agent").update(may_pull_from_agents=True),
                   lambda d: _agent(d, "va_status_agent")["exposes"].append({"fact_key": "x", "data_class": "V3"}),
                   lambda d: d["benefits"][0].update(record_status="VERIFIED"),
                   lambda d: d["governance"]["publish_policy"]["environments"].update(production="preview_unverified"),
                   lambda d: d["counts"].update(verified=1)):
        data = copy.deepcopy(raw)
        mutate(data)
        assert list(validator.iter_errors(data))


def test_generated_records_cannot_claim_verified(raw):
    data = copy.deepcopy(raw)
    data["benefits"][0]["record_status"] = "VERIFIED"
    with pytest.raises(RegistryError, match="VERIFIED"):
        VaultRegistry(restamp(data), check_schema=False)


def test_noncanonical_rule_is_refused(raw):
    data = copy.deepcopy(raw)
    item = next(b for b in data["benefits"] if " & " in b["rule"])
    item["rule"] = item["rule"].replace(" & ", "&", 1)
    with pytest.raises(RegistryError, match="canonical"):
        VaultRegistry(restamp(data), check_schema=False)


def test_outcomes_and_facts_must_match_code(raw):
    data = copy.deepcopy(raw)
    data["vocabulary"]["outcomes"] = list(OUTCOMES)[:-1] + ["APPROVED"]
    with pytest.raises(RegistryError, match="outcome"):
        VaultRegistry(restamp(data), check_schema=False)
    data = copy.deepcopy(raw)
    data["facts"]["va_rating"]["data_class"] = "V1"
    with pytest.raises(RegistryError, match="fact catalog"):
        VaultRegistry(restamp(data), check_schema=False)


def test_reviews_apply_only_to_unchanged_content(registry):
    benefit = registry.benefits["tx.hazlewood-act-for-veterans"]
    good = Review(benefit.benefit_id, "reviewer-01", "2026-10-28", benefit.content_hash)
    stale = Review("us.fry-scholarship", "reviewer-01", "2026-10-28", "0" * 64)
    nameless = Review("us.death-gratuity", "  ", "2026-10-28", registry.benefits["us.death-gratuity"].content_hash)
    # A reviewer is a roster handle, never a personal name or an email address.
    named = Review("us.post-9-11-gi-bill-chapter-33", "Jane Doe", "2026-10-28",
                   registry.benefits["us.post-9-11-gi-bill-chapter-33"].content_hash)
    emailed = Review("us.fry-scholarship", "reviewer@example.org", "2026-10-28",
                     registry.benefits["us.fry-scholarship"].content_hash)
    reviewed = registry.with_reviews([good, stale, nameless, named, emailed])
    assert reviewed.benefits[benefit.benefit_id].record_status == "VERIFIED"
    assert reviewed.benefits[benefit.benefit_id].verified_by == "reviewer-01"
    assert reviewed.benefits["us.fry-scholarship"].record_status != "VERIFIED"
    assert reviewed.stale_reviews == ("us.death-gratuity", "us.fry-scholarship", "us.post-9-11-gi-bill-chapter-33")
    assert registry.benefits[benefit.benefit_id].record_status != "VERIFIED"


def test_publish_policy_by_environment(registry, monkeypatch):
    monkeypatch.delenv("VETBUDDY_ENV", raising=False)
    assert registry.publish_policy() == "verified_only"
    assert registry.publish_policy("development") == "preview_unverified"
    assert registry.publish_policy("unknown-env") == "verified_only"
    monkeypatch.setenv("VETBUDDY_ENV", "test")
    assert registry.publish_policy() == "preview_unverified"
