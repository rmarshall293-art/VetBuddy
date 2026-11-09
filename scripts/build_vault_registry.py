#!/usr/bin/env python3
"""Build the Benefit Vault registry, or check it for drift.

    python3 scripts/build_vault_registry.py           # write the registry
    python3 scripts/build_vault_registry.py --check   # exit 1 if the file differs

Inputs: the research ledgers (data/research/states, data/research/federal),
the recovered leads (data/research/recovered) and the authored policy
(config/benefit_vault_policy.yaml). Output: one canonical file,
data/reference/benefit_vault_registry.json, integrity-stamped and valid
against schemas/json/benefit_vault_registry.schema.json.

The build is deterministic: the same inputs give byte-identical output.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.domains.vault import facts as fact_catalog  # noqa: E402
from app.domains.vault import rules, vocab  # noqa: E402
from app.domains.vault.canonical import canonical_json, sha256_hex  # noqa: E402
from app.domains.vault.discovery import importer  # noqa: E402
from app.domains.vault.guards import LanguageGuard  # noqa: E402

REGISTRY_PATH = ROOT / "data" / "reference" / "benefit_vault_registry.json"
SCHEMA_PATH = ROOT / "schemas" / "json" / "benefit_vault_registry.schema.json"
POLICY_PATH = ROOT / "config" / "benefit_vault_policy.yaml"
LANGUAGE_PATH = ROOT / "config" / "governance_language.yaml"
RESEARCH_DIR = ROOT / "data" / "research"
RECOVERED_DIR = RESEARCH_DIR / "recovered"
REGISTRY_NAME = "vetbuddy.benefit_vault_registry"
GOVERNING_SENTENCE = "Agents orchestrate, gather and explain; they never decide."


class BuildError(RuntimeError):
    pass


def load_policy() -> dict:
    return yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))


def load_notice(policy: dict) -> str:
    """The v6 common notice, from the one governance language file (never restated in the policy)."""
    if policy.get("notice_from") != "governance_language.common_notice":
        raise BuildError("policy notice_from must be governance_language.common_notice")
    language = yaml.safe_load(LANGUAGE_PATH.read_text(encoding="utf-8"))
    notice = language.get("common_notice")
    if not notice:
        raise BuildError("config/governance_language.yaml has no common_notice")
    return " ".join(notice.split())


def _manifest_entries() -> dict:
    manifest = json.loads((RECOVERED_DIR / "RECOVERY_MANIFEST.json").read_text(encoding="utf-8"))
    return {entry["path"]: entry for entry in manifest["entries"]}


def _read_recovered(rel: str, entries: dict):
    path = RECOVERED_DIR / rel
    entry = entries.get(rel)
    if entry is None:
        raise BuildError(f"{rel} is not in RECOVERY_MANIFEST.json")
    data = path.read_bytes()
    if sha256_hex(data) != entry["sha256"]:
        raise BuildError(f"{rel} does not match its recovery manifest hash")
    return json.loads(data.decode("utf-8")), entry


def build_rule_leads(entries: dict) -> list:
    data, entry = _read_recovered("slice02/guard_reserve.json", entries)
    leads = []
    for item in data["rule_leads"]:
        status = item["status"]
        if status not in vocab.RECORD_STATUSES or status == "VERIFIED":
            raise BuildError(f"rule lead {item['id']} has status {status}")
        leads.append({
            "lead_id": item["id"],
            "topic": item["benefit"],
            "citation": item["citation"],
            "lead": item["lead"],
            "caveat": item.get("caveat"),
            "correction_on_record": item.get("correction_on_record"),
            "record_status": status,
            "source": {"recovered_from": entry["recovered_from"], "path": "slice02/guard_reserve.json"},
        })
    return sorted(leads, key=lambda lead: lead["lead_id"])


def build_recovered_leads(entries: dict, cross_checks: dict, benefit_ids: set) -> list:
    leads = []
    demo, demo_entry = _read_recovered("zip_recreation/demo_recreation_13.json", entries)
    for item in demo:
        leads.append({
            "lead_id": item["id"],
            "title": item["name"],
            "organization": item["org"],
            "jurisdiction": "US" if item["st"] == "National" else item["st"],
            "claim": f"{item['det']} Who: {item['elig']}",
            "url": item.get("web"),
            "record_status": "ILLUSTRATIVE",
            "tier": 4,
            "dataset": "zip_recreation/demo_recreation_13.json",
            "recovered_from": demo_entry["recovered_from"],
        })
    seed, seed_entry = _read_recovered("zip_recreation/recreation_seed_10.json", entries)
    for index, item in enumerate(seed, start=1):
        name, _category, _state, org, url, _kind, description = item[:7]
        leads.append({
            "lead_id": f"RS{index:02d}",
            "title": name,
            "organization": org,
            "jurisdiction": "US",
            "claim": description,
            "url": url,
            "record_status": "UNVERIFIED",
            "tier": 4,
            "dataset": "zip_recreation/recreation_seed_10.json",
            "recovered_from": seed_entry["recovered_from"],
        })
    for lead in leads:
        check = cross_checks.get(lead["lead_id"])
        if check is None:
            raise BuildError(f"recovered lead {lead['lead_id']} has no cross-check in the policy")
        target = check.get("benefit_id")
        if target is not None and target not in benefit_ids:
            raise BuildError(f"cross-check for {lead['lead_id']} names unknown record {target}")
        if check["relation"] not in ("agrees", "differs", "none"):
            raise BuildError(f"cross-check for {lead['lead_id']} has relation {check['relation']}")
        lead["cross_check"] = {"benefit_id": target, "relation": check["relation"], "note": check.get("note")}
        if lead["url"] is not None and not str(lead["url"]).startswith("https://"):
            lead["url"] = None
    extra = set(cross_checks) - {lead["lead_id"] for lead in leads}
    if extra:
        raise BuildError(f"cross-checks name unknown leads: {sorted(extra)}")
    return sorted(leads, key=lambda lead: lead["lead_id"])


def build_license_reciprocity(entries: dict) -> dict:
    data, entry = _read_recovered("zip_guard_reserve/license_reciprocity_51.json", entries)
    states = {}
    for code, (teacher, lawyer, real_estate) in sorted(data.items()):
        if code not in vocab.JURISDICTIONS or code == "US":
            raise BuildError(f"license reciprocity names unknown state {code}")
        if real_estate not in ("Full", "Partial", "None"):
            raise BuildError(f"license reciprocity {code} real estate value {real_estate}")
        states[code] = {"teacher_full_reciprocity": bool(teacher), "lawyer_ube": bool(lawyer),
                        "real_estate": real_estate.lower()}
    return {
        "record_status": "UNVERIFIED",
        "tier": 4,
        "note": "Recovered from an earlier VetBuddy dataset. A lead for spouses and members who move; confirm with the state licensing board.",
        "recovered_from": entry["recovered_from"],
        "states": states,
    }


def build_recovered_datasets(entries: dict) -> list:
    """Every recovered dataset, with how the vault uses it and a hash check."""
    out = []
    for path, entry in sorted(entries.items()):
        if entry.get("shipped"):
            data = (RECOVERED_DIR / path).read_bytes()
            if sha256_hex(data) != entry["sha256"]:
                raise BuildError(f"{path} does not match its recovery manifest hash")
            location = f"data/research/recovered/{path}"
        elif entry.get("shipped_as"):
            data = (ROOT / entry["shipped_as"]).read_bytes()
            if sha256_hex(data) != entry["sha256"]:
                raise BuildError(f"{entry['shipped_as']} does not match the recovered {path}")
            location = entry["shipped_as"]
        else:
            location = None
        out.append({
            "path": path,
            "location": location,
            "tier": entry["tier"],
            "sha256": entry["sha256"],
            "recovered_from": entry["recovered_from"],
            "vault_use": entry["vault_use"],
        })
    return out


def build_agents(policy: dict) -> list:
    agents = []
    for manifest in policy["agents"]:
        exposes = []
        for item in manifest["exposes"]:
            key = item["fact_key"]
            spec = fact_catalog.CATALOG.get(key)
            if spec is None:
                raise BuildError(f"{manifest['agent_id']} exposes unknown fact {key}")
            if item["data_class"] != spec.data_class:
                raise BuildError(f"{manifest['agent_id']} exposes {key} as {item['data_class']}, catalog says {spec.data_class}")
            if not spec.pullable or spec.data_class in vocab.NEVER_PULLABLE:
                raise BuildError(f"{manifest['agent_id']} exposes {key}, which may never travel")
            exposes.append({"fact_key": key, "data_class": spec.data_class})
        agents.append({**manifest, "exposes": sorted(exposes, key=lambda e: e["fact_key"])})
    return sorted(agents, key=lambda a: a["agent_id"])


def build_jurisdictions(benefits: list, sources: list, tail_reads: list) -> list:
    counts = Counter(b["jurisdiction"] for b in benefits)
    by_jur = {}
    for benefit in benefits:
        by_jur.setdefault(benefit["jurisdiction"], set()).add(benefit["source_id"])
    source_map = {s["source_id"]: s for s in sources}
    tails = {t["jurisdiction"] for t in tail_reads}
    out = []
    for code, name in vocab.JURISDICTIONS.items():
        ids = sorted(by_jur.get(code, ()))
        out.append({
            "code": code,
            "name": name,
            "coverage": "COVERED" if counts.get(code) else "SOURCE_NOT_AVAILABLE",
            "benefit_count": counts.get(code, 0),
            "source_ids": ids,
            "tail_read": code in tails,
            "tail_unread_chars": sum(source_map[i]["tail_unread_chars"] for i in ids),
        })
    return out


def vocabulary() -> dict:
    return {
        "outcomes": list(vocab.OUTCOMES),
        "record_statuses": list(vocab.RECORD_STATUSES),
        "build_statuses": list(vocab.BUILD_STATUSES),
        "data_classes": list(vocab.DATA_CLASSES),
        "categories": {code: vocab.CATEGORY_LABELS[code] for code in vocab.CATEGORIES},
        "state_categories": list(vocab.STATE_CATEGORIES),
        "groups": dict(vocab.GROUP_LABELS),
        "kinds": list(vocab.KINDS),
        "page_statuses": list(vocab.PAGE_STATUSES),
        "url_statuses": list(vocab.URL_STATUSES),
        "tiers": {
            "1": "the administering government body's own page, or official law text",
            "2": "an official summary or aggregator, or an unofficial copy of the law",
            "3": "the program operator's own page (nonprofit, association or vendor)",
            "4": "a secondary source or a recovered lead",
        },
        "tokens": dict(rules.PLAIN_TOKENS),
        "parametric_tokens": {name: spec[3] for name, spec in rules.PARAM_TOKENS.items()},
        "token_facts": {name: sorted(keys) for name, keys in fact_catalog.TOKEN_FACTS.items()},
        "saved_statuses": list(vocab.SAVED_STATUSES),
        "events": list(vocab.VAULT_EVENTS),
        "denial_reasons": list(vocab.DENIAL_REASONS),
    }


def language_check(registry: dict) -> None:
    guard = LanguageGuard()
    texts = [registry["notice"]] + list(registry["caveats"].values())
    for benefit in registry["benefits"]:
        texts += [benefit["title"], benefit["who_it_is_for"], benefit["value"]]
    for lead in registry["rule_leads"]:
        texts += [lead["lead"], lead.get("caveat") or ""]
    found = guard.check_all(texts)
    if found:
        lines = "\n".join(f"  {v.category}: {v.text[:120]}" for v in found)
        raise BuildError(f"prohibited language in registry text:\n{lines}")


def validate_schema(registry: dict) -> None:
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(registry), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        raise BuildError(f"schema: {first.message} at {'/'.join(str(p) for p in first.path)} ({len(errors)} errors)")


def build() -> dict:
    policy = load_policy()
    _, (sources, benefits, tail_reads) = importer.load_all(RESEARCH_DIR, policy["as_of"])
    benefit_ids = {b["benefit_id"] for b in benefits}
    entries = _manifest_entries()
    rule_leads = build_rule_leads(entries)
    lead_ids = {lead["lead_id"] for lead in rule_leads}
    for benefit_id, links in policy["lead_links"].items():
        if benefit_id not in benefit_ids:
            raise BuildError(f"lead_links names unknown record {benefit_id}")
        if set(links) - lead_ids:
            raise BuildError(f"lead_links for {benefit_id} names unknown leads")
    for benefit_id, caveat_ids in policy["record_caveats"].items():
        if benefit_id not in benefit_ids:
            raise BuildError(f"record_caveats names unknown record {benefit_id}")
        if set(caveat_ids) - set(policy["caveats"]):
            raise BuildError(f"record_caveats for {benefit_id} names unknown caveats")
    for benefit in benefits:
        benefit["lead_ids"] = sorted(policy["lead_links"].get(benefit["benefit_id"], []))
        benefit["caveat_ids"] = sorted(policy["record_caveats"].get(benefit["benefit_id"], []))
    hosts = sorted({importer.host_of(s["url"]) for s in sources if s["url"]}
                   | {importer.host_of(b["official_url"]) for b in benefits})
    registry = {
        "registry": REGISTRY_NAME,
        "version": policy["version"],
        "as_of": policy["as_of"],
        "governing_sentence": GOVERNING_SENTENCE,
        "notice": load_notice(policy),
        "vocabulary": vocabulary(),
        "facts": fact_catalog.catalog_view(),
        "jurisdictions": build_jurisdictions(benefits, sources, tail_reads),
        "sources": sources,
        "benefits": sorted(benefits, key=lambda b: b["benefit_id"]),
        "rule_leads": rule_leads,
        "recovered_leads": build_recovered_leads(entries, policy["recovered_cross_checks"], benefit_ids),
        "license_reciprocity": build_license_reciprocity(entries),
        "recovered_datasets": build_recovered_datasets(entries),
        "governance": {
            "publish_policy": policy["publish_policy"],
            "review": policy["review"],
            "grants": policy["grants"],
            "packets": policy["packets"],
            "mode_ceiling": dict(vocab.MODE_CEILING),
            "never_pullable": sorted(vocab.NEVER_PULLABLE),
            "pull_purposes": list(vocab.PULL_PURPOSES),
            "agents": build_agents(policy),
            "egress_allowlist": hosts,
            "discovery": policy["discovery"],
            "tier_hosts": {
                "tier2": sorted(importer.TIER2_HOSTS),
                "commercial": sorted(importer.COMMERCIAL_HOSTS),
                "nonprofit": sorted(importer.NONPROFIT_HOSTS),
                "mwr_operator": sorted(importer.MWR_OPERATOR_HOSTS),
            },
        },
        "caveats": {key: " ".join(text.split()) for key, text in sorted(policy["caveats"].items())},
        "components": policy["components"],
        "tail_reads": sorted(tail_reads, key=lambda t: (t["jurisdiction"], t["ledger"])),
    }
    registry["counts"] = {
        "benefits": len(benefits),
        "sources": len(sources),
        "sources_opened": sum(1 for s in sources if s["page_status"] == "OPENED"),
        "jurisdictions_covered": sum(1 for j in registry["jurisdictions"] if j["coverage"] == "COVERED"),
        "by_kind": dict(sorted(Counter(b["kind"] for b in benefits).items())),
        "by_record_status": dict(sorted(Counter(b["record_status"] for b in benefits).items())),
        "by_category": dict(sorted(Counter(b["category"] for b in benefits).items())),
        "by_url_status": dict(sorted(Counter(b["official_url_status"] for b in benefits).items())),
        "rule_leads": len(rule_leads),
        "recovered_leads": len(registry["recovered_leads"]),
        "verified": sum(1 for b in benefits if b["record_status"] == "VERIFIED"),
    }
    language_check(registry)
    registry["integrity"] = {
        "algorithm": "sha256",
        "canonical": "JSON with sorted keys, separators (',', ':'), UTF-8, no NaN; the integrity member excluded",
        "sha256": sha256_hex(canonical_json(registry)),
    }
    validate_schema(registry)
    return registry


def render(registry: dict) -> str:
    return json.dumps(registry, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the registry on disk differs")
    args = parser.parse_args(argv)
    try:
        text = render(build())
    except (BuildError, importer.LedgerError) as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 2
    if args.check:
        current = REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else ""
        if current != text:
            print("registry drift: run scripts/build_vault_registry.py", file=sys.stderr)
            return 1
        print("registry up to date")
        return 0
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {REGISTRY_PATH.relative_to(ROOT)} ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
