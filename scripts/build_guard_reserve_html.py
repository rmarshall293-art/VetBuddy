#!/usr/bin/env python3
"""Build dist/vetbuddy-guard-reserve.html: the Guard & Reserve agent as one
self-contained page for the synthetic test environment.

The page shows the agent's own results; it never matches anything itself.
Matching is the server's deterministic kernel (ADR 0006/0011), so this script
runs GuardReserveAgent.match for each synthetic profile in
data/synthetic/guard_reserve_personas.json, in both the production and the
development environment, and writes a compact copy of those envelopes (each
with the agent's own input and output hashes) beside the role's record
catalog. Fixed clock, sorted keys: the build is byte-for-byte repeatable.

  scripts/build_guard_reserve_html.py           write the page
  scripts/build_guard_reserve_html.py --check   fail if the page is out of date
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.domains.vault.agent import BenefitVaultAgent, Session  # noqa: E402
from app.domains.vault.guard_reserve.agent import GuardReserveAgent  # noqa: E402
from app.domains.vault.registry import default_registry  # noqa: E402

OUT = ROOT / "dist" / "vetbuddy-guard-reserve.html"
PERSONAS = ROOT / "data" / "synthetic" / "guard_reserve_personas.json"
NOW = dt.datetime(2026, 11, 25, 17, 0, tzinfo=dt.timezone.utc)   # fixed: deterministic build
ENVIRONMENTS = ("production", "development")
REC_COLS = ["benefit_id", "jurisdiction", "category", "title", "who_it_is_for", "value", "official_url",
            "record_status", "source_tier"]


def _intern(table: dict, value) -> int:
    key = json.dumps(value, sort_keys=True)
    if key not in table:
        table[key] = len(table)
    return table[key]


def build_data() -> dict:
    reg_json = json.loads((ROOT / "data/reference/benefit_vault_registry.json").read_text(encoding="utf-8"))
    registry = default_registry()
    personas = json.loads(PERSONAS.read_text(encoding="utf-8"))
    roles = {e: GuardReserveAgent(BenefitVaultAgent(registry, environment=e)) for e in ENVIRONMENTS}
    session = Session(mode="A", tenant_ref="synthetic")
    catalog = roles["production"].catalog(session)

    selected = {bid for bid, b in registry.benefits.items() if roles["production"].is_guard_reserve(b)}
    strings: dict = {}      # interned texts: reasons, questions, caveats
    leads: dict = {}
    out_personas, used = [], set()
    for p in personas["personas"]:
        entry = {"id": p["id"], "label": p["label"], "summary": p["summary"], "request": p["request"], "env": {}}
        for e in ENVIRONMENTS:
            env = roles[e].match(p["request"], session, NOW)
            if e == "production":
                entry["classification"] = env["classification"]
                entry["conflicts"] = env["subject"]["conflicts"]
                entry["scope"] = env["scope"]
                for lead in env["recovered_leads"]["jurisdictions"] + env["recovered_leads"]["federal"]:
                    leads[lead["lead_id"]] = lead
                entry["leads"] = [x["lead_id"] for x in env["recovered_leads"]["jurisdictions"]]
            items = []
            for i in env["items"]:
                used.add(i["benefit_id"])
                caveats = [_intern(strings, c["text"]) for c in i["caveats"] + i["guard_reserve"]["role_caveats"]]
                items.append([i["benefit_id"], i["outcome"], 1 if i["guard_reserve"]["section"] == "guard_reserve" else 0,
                              [_intern(strings, r) for r in i["reasons"]],
                              [_intern(strings, f["question"]) for f in i["facts_needed"]], caveats])
            entry["env"][e] = {
                "hashes": env["hashes"], "counts": env["counts"], "section_counts": env["section_counts"],
                "evaluated": env["evaluated"], "items": items,
                "checks": [{k: x.get(k) for k in ("kind", "topic", "citation", "lead", "lead_caveat", "outcome", "applies")}
                           | {"caveats": [c["text"] for c in x.get("caveats", [])]} for x in env["rule_lead_checks"]],
                "questions": [q["question"] for q in env["questions"][:6]],
                "general_caveats": [g["text"] for g in env["general_caveats"]],
            }
        out_personas.append(entry)

    benefits = {b["benefit_id"]: b for b in reg_json["benefits"]}
    keep = sorted(selected | used)
    records = [[benefits[bid][c] for c in REC_COLS] + [1 if bid in selected else 0] for bid in keep]
    crisis = yaml.safe_load((ROOT / "config/crisis_floor.yaml").read_text(encoding="utf-8"))
    sample = roles["production"].match(personas["personas"][0]["request"], session, NOW)["recovered_leads"]
    return {
        "built_at": NOW.isoformat(),
        "synthetic_notice": personas["notice"],
        "personas_version": personas["version"],
        "registry": {"version": reg_json["version"], "as_of": reg_json["as_of"], "sha256": reg_json["integrity"]["sha256"],
                     "records": len(reg_json["benefits"])},
        "engine": catalog["engine"], "role": catalog["role"], "notice": catalog["notice"],
        "governing_rule": catalog["governing_rule"], "manifest": catalog["manifest"],
        "components": catalog["components"], "duty_statuses": catalog["duty_statuses"],
        "authorities": catalog["authorities"], "research_gaps": catalog["research_gaps"],
        "jurisdictions": {j["code"]: j["name"] for j in reg_json["jurisdictions"]},
        "categories": reg_json["vocabulary"]["categories"],
        "cols": REC_COLS + ["selected"], "records": records,
        "strings": [json.loads(k) for k, _ in sorted(strings.items(), key=lambda kv: kv[1])],
        "leads": leads, "leads_notice": sample["notice"],
        "federal_leads": [x["lead_id"] for x in sample["federal"]],
        "personas": out_personas,
        "crisis": crisis,
    }


def render(data: dict) -> str:
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    tpl = (ROOT / "web" / "guard_reserve_standalone.html").read_text(encoding="utf-8")
    page = tpl.replace("/*@@DATA@@*/", "const GR = " + blob + ";")
    digest = hashlib.sha256(blob.encode()).hexdigest()
    return page.replace("@@DATA_SHA256@@", digest)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    page = render(build_data())
    if "--check" in argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != page:
            print("guard-reserve page drift: run scripts/build_guard_reserve_html.py", file=sys.stderr)
            return 1
        print("guard-reserve page up to date")
        return 0
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote: {OUT.relative_to(ROOT)} ({len(page.encode()):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
