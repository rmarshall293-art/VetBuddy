#!/usr/bin/env python3
"""Extract the 56-jurisdiction table from the owner-supplied Gemini Guard & Reserve report.

Input:  data/research/recovered/gemini_guard_reserve/report.html (hash-pinned in
        RECOVERY_MANIFEST.json; an AI-written report, tier 4)
Output: data/research/recovered/gemini_guard_reserve/jurisdictions_56.json

For each jurisdiction the output keeps the report's four cells word for word,
the source the report names for that row (not opened by VetBuddy), tags drawn
from fixed keyword rules, the governance language guard's findings on each
cell, and a cross-check against the Benefit Vault registry: does the vault
already carry the Guard education program the report names? It also checks
the report's own headline counts against its table.

Nothing here becomes a benefit record. The Guard & Reserve role shows these
rows as UNVERIFIED tier 4 leads (ADR 0011 addendum).

    python3 scripts/extract_gemini_guard_reserve.py           # write
    python3 scripts/extract_gemini_guard_reserve.py --check   # fail on drift
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.domains.vault.guards import LanguageGuard  # noqa: E402

DIR = ROOT / "data" / "research" / "recovered" / "gemini_guard_reserve"
REPORT = DIR / "report.html"
OUT = DIR / "jurisdictions_56.json"
REGISTRY = ROOT / "data" / "reference" / "benefit_vault_registry.json"
COLUMNS = ("education", "income_tax", "property_tax", "other")
NAME_ALIASES = {"Washington, D.C.": "DC", "U.S. Virgin Islands": "VI", "Northern Mariana Islands": "MP"}
# Uppercase tokens that are not program names.
NOT_PROGRAMS = {"NG", "UG", "AD", "VA", "FY", "UA", "UW", "CC", "UT", "TA", "FTA", "DE", "ME", "MD", "MA", "NH",
                "NJ", "NY", "PA", "RI", "VT", "AL", "AR", "FL", "GA", "KY", "LA", "MS", "NC", "SC", "TN", "WV",
                "PR", "USVI", "IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "ND", "OH", "SD", "WI", "AK", "AZ",
                "CA", "CO", "HI", "ID", "MT", "NV", "NM", "OK", "OR", "TX", "WA", "WY", "UPR", "UVI", "NMC",
                "SUNY", "MU", "CMD", "NSHE", "DC", "II", "CT", "GI"}
TAG_RULES = {
    # AGR named with a rule of its own, not inside the generic "drill/AGR taxed" phrases.
    "agr_specific_rule": r"\bAGR\b",
    "mentions_reserve": r"\bRes\b|\bReserv",
    "title_10_32_split": r"Title 10.*Title 32|Title 32.*Title 10",
    "no_state_income_tax": r"No (state|earned-income) (income )?tax",
    "no_national_guard": r"no National Guard|Army Reserve only",
    "report_lists_no_guard_tuition": r"^No territorial|no non-vet NG TA",
}


# Phrases that name AGR only as one of every kind of military pay.
GENERIC_AGR = (r"(?i)drill(/| ?, ?)AGR( & retired pay)?|AD/AGR|NG/Res/AGR(/Tech)?|"
               r"\(drill, AGR & retired pay untaxed\)")


class TableParser(HTMLParser):
    """Rows of the first table: (cells, first link in the row)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = 0
        self.rows, self.row, self.cell, self.href = [], None, None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tables += 1
        if self.tables != 1:
            return
        if tag == "tr":
            self.row, self.href = [], None
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
        elif tag == "a" and self.row is not None and self.href is None:
            self.href = dict(attrs).get("href")

    def handle_endtag(self, tag):
        if self.tables != 1:
            return
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append((self.row, self.href))
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def program_token(text: str):
    for tok in re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", text):
        if tok not in NOT_PROGRAMS:
            return tok
    return None


def build() -> dict:
    raw = REPORT.read_bytes()
    parser = TableParser()
    parser.feed(raw.decode("utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    codes = {j["name"]: j["code"] for j in registry["jurisdictions"]}
    codes.update(NAME_ALIASES)
    by_jur = {}
    for b in registry["benefits"]:
        by_jur.setdefault(b["jurisdiction"], []).append(b)
    guard = LanguageGuard()

    rows, region = [], None
    for cells, href in parser.rows:
        if len(cells) == 1:
            region = re.sub(r"\s*\(\d+ Jurisdictions\)", "", cells[0])
            continue
        if len(cells) != 5 or cells[0] == "Jurisdiction":
            continue
        name = cells[0]
        code = codes.get(name)
        if code is None:
            raise SystemExit(f"unknown jurisdiction in report: {name}")
        cell = dict(zip(COLUMNS, cells[1:]))
        joined = " | ".join(cell.values())
        agr_text = re.sub(GENERIC_AGR, "", joined)
        target = {"report_lists_no_guard_tuition": cell["education"], "agr_specific_rule": agr_text}
        tags = sorted(t for t, rx in TAG_RULES.items() if re.search(rx, target.get(t, joined)))
        flags = {col: sorted({v.category for v in guard.violations(text)}) for col, text in cell.items()}
        flags = {k: v for k, v in flags.items() if v}
        program = None if "report_lists_no_guard_tuition" in tags else program_token(cell["education"])
        records = by_jur.get(code, [])
        guard_edu = [b for b in records if b["category"] == "GUARD_EDU"]
        hit = [b["benefit_id"] for b in records if program and re.search(rf"\b{re.escape(program)}\b", b["title"])]
        if "report_lists_no_guard_tuition" in tags:
            relation = "report_lists_none" if not guard_edu else "report_lists_none_vault_has_record"
        elif hit:
            relation = "program_in_vault"
        elif guard_edu:
            relation = "vault_has_guard_education_record"
        else:
            relation = "not_in_vault"
        rows.append({"code": code, "name": name, "region": region, **cell,
                     "named_source": href, "tags": tags, "language_flags": flags,
                     "cross_check": {"program": program, "relation": relation, "matching_records": hit,
                                     "vault_guard_education_records": len(guard_edu)}})
    if len(rows) != 56 or len({r["code"] for r in rows}) != 56:
        raise SystemExit(f"expected 56 distinct jurisdictions, found {len(rows)}")
    rows.sort(key=lambda r: r["code"])

    with_tuition = sum("report_lists_no_guard_tuition" not in r["tags"] for r in rows)
    no_tax = sum("no_state_income_tax" in r["tags"] for r in rows)
    consistency = [
        {"claim": "51 / 56 jurisdictions offer dedicated National Guard tuition waivers or assistance",
         "table_count": with_tuition,
         "agrees": with_tuition == 51,
         "note": "Rows whose education cell does not start with 'No territorial' or say 'no non-vet NG TA'."},
        {"claim": "9 jurisdictions have no earned-income tax", "table_count": no_tax, "agrees": no_tax == 9,
         "note": "Rows whose tax cell says 'No state income tax' or 'No earned-income tax'."},
    ]
    relations = {}
    for r in rows:
        relations[r["cross_check"]["relation"]] = relations.get(r["cross_check"]["relation"], 0) + 1
    return {
        "dataset": "vetbuddy.recovered.gemini_guard_reserve.jurisdictions_56",
        "version": "1.0.0",
        "extracted_from": "data/research/recovered/gemini_guard_reserve/report.html",
        "report_sha256": hashlib.sha256(raw).hexdigest(),
        # The registry's own hash covers the recovery manifest, which covers this file;
        # the cross-check depends only on the benefit records, so it pins those.
        "registry_benefits_sha256": hashlib.sha256(json.dumps(registry["benefits"], sort_keys=True,
                                                              ensure_ascii=False).encode("utf-8")).hexdigest(),
        "record_status": "UNVERIFIED",
        "tier": 4,
        "notice": ("Cells are the report's own words. The report is AI-written; it names a source for each row, "
                   "which VetBuddy has not opened. Leads to check, never benefit records."),
        "tag_rules": TAG_RULES,
        "generic_agr_phrases": GENERIC_AGR,
        "relations": {
            "program_in_vault": "a vault record in this jurisdiction names the program the report names",
            "vault_has_guard_education_record": "the vault has a Guard education record here; whether it is the same program is not confirmed",
            "not_in_vault": "the report names a Guard education program and the vault has none here: research target",
            "report_lists_none": "the report says there is no territorial Guard tuition program, and the vault has none",
            "report_lists_none_vault_has_record": "the report says there is none, but the vault has a record: a conflict to review",
        },
        "report_consistency": consistency,
        "cross_check_counts": dict(sorted(relations.items())),
        "jurisdictions": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = json.dumps(build(), indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("STALE (run scripts/extract_gemini_guard_reserve.py):", OUT.relative_to(ROOT))
            return 1
        print("up to date")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
