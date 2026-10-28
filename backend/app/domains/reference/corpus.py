"""Load, validate and flatten the reference corpus (data/reference/*.json).

Pure: reads files, returns rows. No database, no clock, no network. The
same function feeds the seed generator (scripts/build_reference.py) and the
tests, so the database can never hold a row the validator did not see.

Validation is the integration's redundancy and honesty gate:
  * every id is ASCII and unique per table; every source is registered;
  * every jurisdiction is one of the 57 in migration 0003;
  * dedupe keys: directory (kind, jurisdiction, name, place); statistics
    (jurisdiction, metric, period, source); education programs by name;
  * no retired crisis number anywhere; a directory phone equal to a crisis
    floor number must say so (also_in_crisis_floor) — the floor is authored
    once, in config/crisis_floor.yaml;
  * mailboxes are role mailboxes, never first.last personal addresses;
  * money is integer cents; VERIFIED needs a named reviewer (none exist);
  * every conflict keeps >= 2 readings and every reference to one resolves;
  * user-facing text passes the ClaimsBoundaryGuard pattern scan.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.domains.reference import claims_boundary
from app.domains.reference.phone import normalize_phone
from app.platform.crisis_floor import load_crisis_contacts, retired_numbers

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "data" / "reference"
MIGRATION_0003 = ROOT / "database" / "migrations" / "0003_jurisdiction_benefits_resources.sql"

STATUSES = ("UNVERIFIED", "SOURCE_CHECKED", "CONTESTED", "SUPERSEDED", "VERIFIED", "ILLUSTRATIVE", "HEURISTIC")
REPO_STATUSES = ("IMPLEMENTED_TESTED", "IMPLEMENTED_UNVERIFIED", "PARTIAL", "MOCK", "PLANNED",
                 "DISABLED", "BLOCKED")  # master prompt v6 §0; SQL CHECK in migration 0012
DATASET_FILES = ("sources", "women_veterans", "compensation", "state_benefits", "guard_reserve", "alabama",
                 "statistics", "conflicts", "transition_timeline", "education", "governance", "modules",
                 "rating_schedule")
_ID = re.compile(r"^[A-Za-z0-9_.:\-/]+$")
_PERSONAL_MAILBOX = re.compile(r"^[a-z]+[._][a-z][a-z\-]+\d*@", re.I)
# Text fields shown to veterans; scanned for prohibited claim language.
USER_FACING = ("eligibility_note", "caveat", "text", "lead", "statement", "detail", "item", "stacking_notes")


class CorpusError(ValueError):
    pass


@dataclass
class Corpus:
    tables: dict[str, list[dict]] = field(default_factory=dict)
    datasets: list[dict] = field(default_factory=list)
    raw: dict[str, dict] = field(default_factory=dict)

    def add(self, table: str, row: dict) -> None:
        self.tables.setdefault(table, []).append(row)


def known_jurisdictions() -> list[dict]:
    """The 57 rows seeded by migration 0003 (single parser; build_web uses it too)."""
    sql = MIGRATION_0003.read_text()
    rows = re.findall(r"\('([A-Z]+)','([^']+)','(federal|state|territory)','(\w+)'\)", sql)
    out = [{"code": c, "name": n, "kind": k, "verification_status": v} for c, n, k, v in rows]
    if len(out) != 57:
        raise CorpusError(f"expected 57 jurisdictions in 0003, parsed {len(out)}")
    return out


def _read(name: str) -> tuple[dict, str]:
    raw = (DATA / f"{name}.json").read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _status(rec: dict, default: str) -> str:
    return rec.get("status") or default


def _cents(dollars: int) -> int:
    if not isinstance(dollars, int):
        raise CorpusError(f"whole-dollar value expected, got {dollars!r}")
    return dollars * 100


def build() -> Corpus:
    c = Corpus()
    counts: dict[str, int] = {}
    shas: dict[str, str] = {}
    docs: dict[str, dict] = {}
    for name in DATASET_FILES:
        docs[name], shas[name] = _read(name)
    c.raw = docs

    def track(ds: str, table: str, row: dict) -> None:
        c.add(table, row)
        counts[ds] = counts.get(ds, 0) + 1

    # sources
    for s in docs["sources"]["records"]:
        track("sources", "source", {"source_id": s["id"], "title": s["title"], "kind": s["kind"], "tier": s["tier"],
                                    "as_of": s["as_of"], "origin": s["origin"], "note": s.get("note")})

    # women veterans
    wv = docs["women_veterans"]
    dflt = wv["default_status"]
    for ct in wv["care_types"]:
        track("women_veterans", "care_type", {"code": ct["code"], "label": ct["label"]})

    def directory(kind, rec, jur, **kw):
        row = {"entry_id": rec["id"], "kind": kind, "jurisdiction_code": jur, "name": kw.get("name", rec.get("name")),
               "place": rec.get("place"), "org_type": rec.get("org_type"), "program": kw.get("program"),
               "care_types": kw.get("care_types", rec.get("care_types", [])), "phone": rec.get("phone"),
               "phone_e164": normalize_phone(rec.get("phone")), "text_line": rec.get("text"),
               "mailbox": rec.get("mailbox"), "url": kw.get("url", rec.get("url")),
               "eligibility_note": kw.get("eligibility_note", rec.get("eligibility_note")),
               "caveat": kw.get("caveat", rec.get("caveat")), "dedicated_coordinator": rec.get("dedicated_coordinator"),
               "also_in_crisis_floor": rec.get("also_in_crisis_floor"), "last_checked": kw.get("last_checked", rec.get("last_checked")),
               "status": kw.get("status", _status(rec, dflt)), "source_ids": kw.get("sources", rec.get("sources"))}
        track("women_veterans", "directory_entry", row)

    for r in wv["facility_roles"]:
        directory("facility_role", r, "FEDERAL", url=r["locator_url"], eligibility_note=r.get("note"))
    for r in wv["national"]:
        directory("national", r, "FEDERAL")
    for r in wv["state_offices"]:
        note = " ".join(x for x in (r.get("note"),) if x) or None
        directory("state_office", r, r["jurisdiction"], name=r["agency"], program=r["program"],
                  care_types=["wv_state_coord"], eligibility_note=note, sources=wv["state_offices_sources"])
    meta = wv["territory_dv_coalitions_meta"]
    for r in wv["territory_dv_coalitions"]:
        cav = " ".join(x for x in (meta["phone_policy"], r.get("caveat")) if x)
        directory("territory_dv_coalition", r, r["jurisdiction"], care_types=["wv_dv_ipv"], url=meta["source_url"],
                  caveat=cav, status=meta["status"], last_checked=meta["last_checked"], sources=meta["sources"])
    meta = wv["mst_residential_programs_meta"]
    for r in wv["mst_residential_programs"]:
        directory("mst_residential", r, r["jurisdiction"], care_types=["wv_mst", "wv_ptsd"],
                  eligibility_note=r.get("note"), caveat=meta["caveat"], status=meta["status"], sources=meta["sources"])
    for r in wv["cohen_clinics"]:
        directory("clinic", r, r["jurisdiction"], name="Cohen Veterans Network clinic",
                  care_types=["wv_ptsd", "wv_mental_health"], eligibility_note=r.get("note"),
                  url="https://www.cohenveteransnetwork.org/", sources=wv["cohen_clinics_sources"])
    for r in wv["eligibility_highlights"]:
        track("women_veterans", "rule_lead", {"lead_id": r["id"], "domain": "women_veterans", "benefit": r["care_type"],
                                              "citation": r["verify_against"], "lead": r["statement"], "caveat": None,
                                              "status": _status(r, dflt), "source_ids": r["sources"]})
    jur_of = {"Kentucky": "KY", "North Dakota": "ND", "Oklahoma": "OK"}
    for i, note in enumerate(wv["dv_coalition_reconciliation"], 1):
        jur = next((code for st, code in jur_of.items() if note.startswith(st) or f" {st}" in note[:40]), "FEDERAL")
        track("women_veterans", "finding", {"finding_id": f"wv.dv_reconcile.{i}", "kind": "data_maintenance",
                                            "jurisdiction_code": jur, "title": "DV coalition directory reconciliation",
                                            "detail": note, "event_date": None, "status": "SOURCE_CHECKED",
                                            "source_ids": ["src.mod.women_veterans"]})

    # compensation
    comp = docs["compensation"]
    src = comp["sources"]
    vc = comp["va_compensation"]
    conflict_cells = {("veteran_alone", 70): "conflict.va_comp.2025_70pct_single"}

    def rate(rate_set, dims, cents, eff_from, *, ds="compensation", rounded=False, status="UNVERIFIED",
             eff_to=None, note=None, conflict=None):
        track(ds, "rate", {"rate_set": rate_set, "dims": dims, "amount_cents": cents, "rounded": rounded,
                           "effective_from": eff_from, "effective_to": eff_to, "note": note, "conflict_id": conflict,
                           "status": "CONTESTED" if conflict else status, "source_ids": src})

    for table in ("veteran_alone", "with_spouse", "with_spouse_and_one_child"):
        for rating, cents in vc[table].items():
            rate(vc["rate_set"], {"dependents": table, "rating": int(rating)}, cents, vc["effective_from"],
                 eff_to=vc["effective_to"], conflict=conflict_cells.get((table, int(rating))))
    for a in vc["addons"]:
        rate(vc["rate_set"], {"addon": a["key"], "rating": a["rating"]}, a["amount_cents"], vc["effective_from"],
             eff_to=vc["effective_to"], rounded=a.get("rounded", False))
    for p in vc["rate_2026_points"]:
        rate("va_comp_2026", {"dependents": p["key"], "rating": p["rating"]}, p["amount_cents"], p["effective_from"],
             note=p.get("note"))
    for v in comp["va_special"]["smc_2025_approximate"]["values"]:
        rate("smc_2025_approx", {"level": v["level"], "kind": v["kind"]}, v["amount_cents"], vc["effective_from"],
             rounded=v.get("rounded", False), status="ILLUSTRATIVE")
    mp = comp["military_pay"]
    gate_conflicts = {("E-8", ">18"), ("E-9", ">18"), ("O-3", ">4")}
    for table in ("enlisted", "officer", "warrant"):
        cols = mp[table]["columns"]
        for grade, values in mp[table]["rows"].items():
            if len(values) != len(cols):
                raise CorpusError(f"base pay {grade}: {len(values)} values for {len(cols)} columns")
            for gate, v in zip(cols, values):
                if v is None:
                    continue
                rate(mp["rate_set"], {"grade": grade, "gate": gate}, _cents(v), mp["effective_from"], rounded=True,
                     conflict="conflict.base_pay.gate_labels" if (grade, gate) in gate_conflicts else None)
    for cap, cents in mp["caps_cents"].items():
        rate("base_pay_caps_2025", {"cap": cap}, cents, mp["effective_from"])
    for b in comp["bas"]:
        for k in ("enlisted_cents", "officer_cents", "bas_ii_enlisted_cents"):
            if k in b:
                rate(b["rate_set"], {"category": k.removesuffix("_cents")}, b[k], b["effective_from"], note=b.get("note"))
    bah = comp["bah_samples_2025"]
    for row in bah["rows"]:
        for grade, v in zip(bah["grades"], row["values"]):
            rate("bah_sample_2025", {"mha": row["mha"], "grade": grade, "dependents": "with"}, _cents(v), "2025-01-01",
                 rounded=True, status="ILLUSTRATIVE", note=row.get("note"))
    for sp in comp["special_pays_2025"]["rows"]:
        for bound in ("min", "max"):
            rate("special_pay_2025", {"pay": sp["pay"], "bound": bound}, _cents(sp[bound]), "2025-01-01", note=sp.get("note"))
    sbp = comp["retirement_systems"]["sbp"]
    rate("sbp_2025", {"item": "low_cost_threshold"}, sbp["low_cost_threshold_cents_2025"], "2025-01-01")

    def lead(ds, lid, domain, benefit, citation, text, status, sources, caveat=None):
        track(ds, "rule_lead", {"lead_id": lid, "domain": domain, "benefit": benefit, "citation": citation,
                                "lead": text, "caveat": caveat, "status": status, "source_ids": sources})

    sp = comp["va_special"]
    lead("compensation", "comp.tdiu", "compensation", "TDIU", "38 CFR 4.16(a)", sp["tdiu"]["rule_text"],
         sp["tdiu"]["status"], sp["tdiu"]["sources"], sp["tdiu"]["note"])
    lead("compensation", "comp.pt_unlocks", "compensation", "Permanent and total (P&T) designation", "38 CFR 3.340 (verify)",
         "; ".join(sp["permanent_and_total_unlocks"]), sp["permanent_and_total_status"], src)
    rs = comp["retirement_systems"]
    for s in rs["systems"]:
        body = "; ".join(f"{k}: {v}" for k, v in s.items() if k not in ("id", "name") and v not in (None, True, False))
        lead("compensation", f"ret.{s['id']}", "retirement", s["name"], "10 U.S.C. (verify per system)", body, rs["status"], src)
    for s in rs["concurrent_receipt"]:
        lead("compensation", f"ret.{s['id']}", "retirement", s["name"], "10 U.S.C. 1413a / 1414 (verify)", s["note"], rs["status"], src)
    lead("compensation", "ret.sbp", "retirement", "Survivor Benefit Plan", "10 U.S.C. 1447–1455 (verify)",
         f"Premium {sbp['premium_pct_of_base']}% of base; survivor receives {sbp['survivor_pct_of_base']}%; paid up after {sbp['paid_up']}. {sbp['dic_offset']} {sbp['note']}",
         rs["status"], src)
    h = comp["income_replacement_heuristics"]
    lead("compensation", "fin.income_replacement", "finance", "Civilian salary comparison heuristics", "none (not DoD-published)",
         h["formula_documented"] + " By grade: " + "; ".join(f"{g['grade']} {g['low_cost']} / {g['high_cost']}" for g in h["by_grade"]),
         h["status"], src, h["note"])
    cl = comp["separation_cliff_items"]
    lead("compensation", "fin.separation_cliff", "finance", "What ends at separation", "DoD Greenbook (verify)",
         "; ".join(cl["items"]), cl["status"], src, cl["note"])

    # state benefits
    sb = docs["state_benefits"]
    for code, mrt, nit, prop, programs in sb["summary"]:
        track("state_benefits", "state_summary", {"jurisdiction_code": code, "military_retirement_tax": mrt,
              "no_state_income_tax": nit, "disabled_veteran_property_tax": prop, "notable_programs": programs,
              "status": sb["default_status"], "source_ids": sb["summary_sources"]})
    for r in sb["records"]:
        track("state_benefits", "benefit_lead", {"lead_id": r["id"], "jurisdiction_code": r["jurisdiction"],
              "category": r["category"], "text": r["text"], "authority": r["authority"], "note": r.get("note"),
              "conflict_id": r.get("conflict"), "status": _status(r, sb["default_status"]), "source_ids": r["sources"]})
    track("state_benefits", "finding", {"finding_id": "sb.decision_framework", "kind": "product_implication",
          "jurisdiction_code": None, "title": "State-selection comparison factors",
          "detail": "; ".join(sb["decision_framework"]), "event_date": None, "status": "UNVERIFIED",
          "source_ids": sb["decision_framework_sources"]})

    # guard / reserve
    gr = docs["guard_reserve"]
    for a in gr["authorities"]:
        track("guard_reserve", "duty_authority", {"authority_id": a["id"], "citation": a["citation"], "label": a["label"],
              "qualifies_ch33": a["qualifies_ch33"], "tier_caveat": a.get("tier_caveat", False),
              "guard_only": a.get("guard_only", False), "coast_guard_only": a.get("coast_guard_only", False),
              "status": gr["default_status"], "source_ids": gr["sources"]})
    for r in gr["rule_leads"]:
        cav = " ".join(x for x in (r.get("caveat"), r.get("correction_on_record")) if x) or None
        lead("guard_reserve", r["id"], "guard_reserve", r["benefit"], r["citation"], r["lead"], r["status"], gr["sources"], cav)

    # alabama
    al = docs["alabama"]
    for i in al["installations"]:
        track("alabama", "installation", {"installation_id": i["id"], "jurisdiction_code": "AL", "name": i["name"],
              "place": i["place"], "branch": i["branch"], "role": i["role"], "approx_population": i["approx_population"],
              "tap_delivery": i["tap_delivery"], "former_name": (i.get("redesignation") or {}).get("from"),
              "status": al["default_status"], "source_ids": i["sources"]})

    def finding(ds, fid, kind, jur, title, detail, sources, event_date=None, status="UNVERIFIED"):
        track(ds, "finding", {"finding_id": fid, "kind": kind, "jurisdiction_code": jur, "title": title,
                              "detail": detail, "event_date": event_date, "status": status, "source_ids": sources})

    for p in al["state_programs"]:
        finding("alabama", p["id"], "state_program", "AL", p["name"], p["detail"], p["sources"])
    for p in al["peer_flagships"]:
        finding("alabama", f"flagship.{p['jurisdiction'].lower()}", "peer_flagship", p["jurisdiction"], p["name"],
                p["detail"], al["peer_flagships_sources"])
    for f in al["oversight_findings"]:
        finding("alabama", f"oversight.{f['id']}", "oversight_finding", "FEDERAL", f["citation"], f["finding"],
                al["oversight_findings_sources"])
    for n, w in enumerate(al["what_works"], 1):
        finding("alabama", f"works.{n}", "what_works", "FEDERAL", "What works in transition", w, al["sources"])
    al_events = ("HB284", "Adkins", "Redstone", "SB70", "Novosel", "AFVEC")
    for n, e in enumerate(al["policy_timeline"], 1):
        jur = "AL" if any(k in e["event"] for k in al_events) else "FEDERAL"
        finding("alabama", f"event.{n:02d}", "policy_event", jur, e["event"].split(":")[0][:80], e["event"],
                al["sources"], event_date=e["date"])
    for n, p in enumerate(al["product_implications"], 1):
        finding("alabama", f"implication.{n}", "product_implication", "AL", "Product implication", p, al["sources"])
    ts = al["tap_structure"]
    lead("alabama", "tap.structure", "tap", "Transition Assistance Program structure", ts["authority"],
         " ".join([ts["start_requirement"], ts["counseling_tiers"], "Core: " + "; ".join(ts["core_curriculum"]) + ".",
                   "Tracks: " + "; ".join(ts["two_day_tracks"]) + ".", ts["capstone"]]), ts["status"], ts["sources"])

    # conflicts first-class (statistics and leads reference them)
    cf = docs["conflicts"]
    for r in cf["records"]:
        srcs = sorted({x["source"] for x in r["readings"]})
        track("conflicts", "conflict", {"conflict_id": r["id"], "subject": r["subject"], "status": r["status"],
              "readings": r["readings"], "why_it_matters": r.get("why_it_matters"), "next_action": r.get("next_action"),
              "resolution": r.get("resolution"), "blocking_for": r.get("blocking_for", []), "source_ids": srcs})
    for r in cf["supersessions"]:
        track("conflicts", "supersession", {"supersession_id": r["id"], "old_value": r["old"], "new_value": r["new"],
              "effective": r.get("effective"), "note": r.get("note"), "source_ids": r["sources"]})

    # statistics
    st = docs["statistics"]
    for r in st["records"]:
        track("statistics", "statistic", {"stat_id": r["id"], "jurisdiction_code": r["jurisdiction"], "metric": r["metric"],
              "value": str(r["value"]), "unit": r["unit"], "period": r["period"], "note": r.get("note"),
              "conflict_id": r.get("conflict"), "status": "CONTESTED" if r.get("conflict") else st["default_status"],
              "source_ids": r["sources"]})

    # timeline
    tl = docs["transition_timeline"]
    for w in tl["windows"]:
        track("transition_timeline", "timeline_window", {"window_id": w["id"], "kind": w["kind"], "anchor": w["anchor"],
              "offset_text": w["offset"], "item": w["item"], "verify_against": w["verify_against"],
              "status": tl["default_status"], "source_ids": w["sources"]})
    for s in tl["preparation_steps"]:
        finding("transition_timeline", f"prep.m{s['months_before']:02d}", "preparation_step", None,
                f"{s['months_before']} months before separation" if s["months_before"] else "Separation day",
                "; ".join(s["steps"]), tl["sources"])

    # education
    ed = docs["education"]
    for p in ed["programs"]:
        track("education", "education_program", {"program_id": p["id"], "name": p["name"], "authority": p["authority"],
              "carried_by": p["carried_by"], "stacking_notes": p.get("stacking_notes"), "note": p.get("note"),
              "is_authority_stub": True, "status": _status(p, ed["default_status"]), "source_ids": ed["sources"]})

    # governance
    gv = docs["governance"]
    for r in gv["non_negotiables"]:
        track("governance", "governance_rule", {"rule_id": r["id"], "family": "non_negotiable", "text": f"{r['name']}. {r['text']}",
              "enforced_by": None, "on_violation": None, "repo_status": None, "note": None, "source_ids": gv["sources"]})
    for r in gv["tier0_rules"]:
        track("governance", "governance_rule", {"rule_id": r["id"], "family": "tier0", "text": r["rule"],
              "enforced_by": r["enforced_by"], "on_violation": r["on_violation"], "repo_status": r["repo_status"],
              "note": r.get("repo_note"), "source_ids": gv["sources"]})
    for r in gv["agent_rules"]:
        track("governance", "governance_rule", {"rule_id": r["id"], "family": "agent_rule", "text": r["rule"],
              "enforced_by": None, "on_violation": None, "repo_status": r["repo_status"],
              "note": f"v2.0 build: {r['v2_0_status']}" + (f". {r['repo_note']}" if r.get("repo_note") else ""),
              "source_ids": gv["sources"]})
    for r in gv["release_gates"]:
        track("governance", "governance_rule", {"rule_id": r["id"], "family": "release_gate", "text": r["gate"],
              "enforced_by": None, "on_violation": None, "repo_status": r["repo_status"], "note": r.get("repo_note"),
              "source_ids": gv["sources"]})

    # modules
    for m in docs["modules"]["records"]:
        track("modules", "module", {"module_id": m["id"], "name": m["name"], "plane_fit": m["plane_fit"],
              "integrated": m["integrated"], "spec_only": m["spec_only"], "counts": m.get("counts", {}),
              "source_ids": m["sources"]})

    # rating schedule (38 CFR Part 4 transcription). Regulation text is VA's wording,
    # so it lives in criteria_text, which the claims-language scan does not read.
    # Symptom keywords are never imported: mapping symptoms to codes is prohibited.
    rs = docs["rating_schedule"]
    for code in rs["codes"]:
        if "keywords" in code or "symptoms" in code:
            raise CorpusError(f"rating_schedule {code['code']}: symptom keywords are prohibited (governance section 5)")
        track("rating_schedule", "rating_code", {"code": code["code"], "name": code["name"], "body_system": code["body_system"],
              "subsection": code.get("subsection"), "cfr_section": code.get("cfr_section"), "notes": code.get("notes") or None,
              "has_criteria": bool(code["has_criteria"]), "status": _status(code, rs["default_status"]),
              "status_note": code.get("status_note"), "source_ids": rs["sources"]})
        for i, t in enumerate(code["criteria"]):
            track("rating_schedule", "rating_criterion", {"criterion_id": f"{code['code']}:{i:02d}", "code": code["code"], "position": i,
                                       "percent": t["percent"], "criteria_text": t["text"]})

    for name in DATASET_FILES:
        d = docs[name]
        c.datasets.append({"dataset_id": name, "title": d["title"], "version": d.get("version", "n/a"),
                           "as_of": d["as_of"], "review_by": d.get("review_by"), "sha256": shas[name],
                           "record_count": counts.get(name, 0)})
    validate(c)
    return c


# ── validation ───────────────────────────────────────────────────────────────

PK = {"source": ("source_id",), "care_type": ("code",), "directory_entry": ("entry_id",), "conflict": ("conflict_id",),
      "supersession": ("supersession_id",), "statistic": ("stat_id",), "rate": ("rate_set", "dims"),
      "state_summary": ("jurisdiction_code",), "benefit_lead": ("lead_id",), "duty_authority": ("authority_id",),
      "rule_lead": ("lead_id",), "timeline_window": ("window_id",), "education_program": ("program_id",),
      "installation": ("installation_id",), "finding": ("finding_id",), "governance_rule": ("rule_id",),
      "module": ("module_id",), "rating_code": ("code",), "rating_criterion": ("criterion_id",)}


def _key(row: dict, cols: tuple[str, ...]):
    return tuple(json.dumps(row[c], sort_keys=True) if isinstance(row[c], dict) else row[c] for c in cols)


def validate(c: Corpus) -> None:
    errors: list[str] = []
    t = c.tables
    sources = {r["source_id"] for r in t.get("source", [])}
    jurisdictions = {j["code"] for j in known_jurisdictions()}
    care_types = {r["code"] for r in t.get("care_type", [])}
    conflicts = {r["conflict_id"] for r in t.get("conflict", [])}
    retired = set(retired_numbers())
    floor = {}
    for k in load_crisis_contacts():
        for f in ("phone",):
            e = normalize_phone(k.get(f))
            if e and len(e) > 6:
                floor[e] = k["key"]

    for table, rows in t.items():
        seen = set()
        for r in rows:
            k = _key(r, PK[table])
            if k in seen:
                errors.append(f"{table}: duplicate key {k}")
            seen.add(k)
            for col in PK[table]:
                if isinstance(r[col], str) and not _ID.match(r[col]):
                    errors.append(f"{table}: non-ASCII or malformed id {r[col]!r}")
            for s in r.get("source_ids") or []:
                if s not in sources:
                    errors.append(f"{table} {k}: unregistered source {s}")
            if "source_ids" in r and not r["source_ids"]:
                errors.append(f"{table} {k}: no source")
            if "status" in r and table not in ("conflict",):
                if r["status"] not in STATUSES:
                    errors.append(f"{table} {k}: bad status {r['status']}")
                if r["status"] == "VERIFIED" and not r.get("verified_by"):
                    errors.append(f"{table} {k}: VERIFIED without a named reviewer")
            jc = r.get("jurisdiction_code")
            if jc is not None and jc not in jurisdictions:
                errors.append(f"{table} {k}: unknown jurisdiction {jc}")
            if r.get("conflict_id") and r["conflict_id"] not in conflicts:
                errors.append(f"{table} {k}: unknown conflict {r['conflict_id']}")
            if "repo_status" in r and r["repo_status"] is not None and r["repo_status"] not in REPO_STATUSES:
                errors.append(f"{table} {k}: bad repo_status {r['repo_status']}")
            for f in USER_FACING:
                if table != "governance_rule" and isinstance(r.get(f), str):
                    for hit in claims_boundary.scan(r[f]):
                        errors.append(f"{table} {k}.{f}: prohibited {hit.category} language '{hit.excerpt}'")

    for r in t.get("directory_entry", []):
        k = r["entry_id"]
        for ct in r["care_types"]:
            if ct not in care_types:
                errors.append(f"directory_entry {k}: unknown care_type {ct}")
        e = r["phone_e164"]
        if r["phone"] and not e:
            errors.append(f"directory_entry {k}: phone {r['phone']!r} does not normalize")
        if e in retired:
            errors.append(f"directory_entry {k}: RETIRED crisis number {r['phone']}")
        if e in floor and r.get("also_in_crisis_floor") != floor[e]:
            errors.append(f"directory_entry {k}: duplicates crisis floor '{floor[e]}' without saying so")
        if r["mailbox"] and _PERSONAL_MAILBOX.match(r["mailbox"]):
            errors.append(f"directory_entry {k}: personal mailbox {r['mailbox']}")
        if r["url"] and not r["url"].startswith("https://"):
            errors.append(f"directory_entry {k}: non-https url")
    natural = {}
    for r in t.get("directory_entry", []):
        nk = (r["kind"], r["jurisdiction_code"], r["name"].lower(), (r["place"] or "").lower())
        if nk in natural:
            errors.append(f"directory_entry {r['entry_id']}: same organization+place as {natural[nk]}")
        natural[nk] = r["entry_id"]
    names = {}
    for r in t.get("education_program", []):
        n = r["name"].lower()
        if n in names:
            errors.append(f"education_program {r['program_id']}: duplicate of {names[n]}")
        names[n] = r["program_id"]
    stat_keys = {}
    for r in t.get("statistic", []):
        sk = (r["jurisdiction_code"], r["metric"], r["period"], tuple(r["source_ids"]))
        if sk in stat_keys:
            errors.append(f"statistic {r['stat_id']}: duplicate of {stat_keys[sk]}")
        stat_keys[sk] = r["stat_id"]
    for r in t.get("conflict", []):
        if r["status"] == "contested_unresolved" and len(r["readings"]) < 2:
            errors.append(f"conflict {r['conflict_id']}: fewer than two readings")
        if r["status"] == "resolved_by_design" and not r.get("resolution"):
            errors.append(f"conflict {r['conflict_id']}: resolved without a resolution")
    for r in t.get("rate", []):
        if not isinstance(r["amount_cents"], int) or isinstance(r["amount_cents"], bool) or r["amount_cents"] < 0:
            errors.append(f"rate {r['rate_set']} {r['dims']}: amount must be non-negative integer cents")
    for r in t.get("benefit_lead", []):
        if r["status"] == "CONTESTED" and not r.get("conflict_id"):
            errors.append(f"benefit_lead {r['lead_id']}: CONTESTED without a conflict id")
    codes = {r["code"] for r in t.get("rating_code", [])}
    for r in t.get("rating_code", []):
        if not re.fullmatch(r"\d{4}", r["code"]):
            errors.append(f"rating_code {r['code']}: diagnostic codes are four digits")
    for r in t.get("rating_criterion", []):
        if r["code"] not in codes:
            errors.append(f"rating_criterion {r['criterion_id']}: unknown code {r['code']}")
        if not (isinstance(r["percent"], int) and 0 <= r["percent"] <= 100 and r["percent"] % 10 == 0):
            errors.append(f"rating_criterion {r['criterion_id']}: percent must be 0-100 in steps of 10")
    summary = {r["jurisdiction_code"] for r in t.get("state_summary", [])}
    expected = {j["code"] for j in known_jurisdictions() if j["kind"] == "state"} | {"DC"}
    if summary != expected:
        errors.append(f"state_summary must cover the 50 states + DC exactly; diff {sorted(summary ^ expected)}")
    for r in t.get("state_summary", []):
        if r["no_state_income_tax"] != (r["military_retirement_tax"] == "no_income_tax"):
            errors.append(f"state_summary {r['jurisdiction_code']}: income-tax flag disagrees with classification")
    if errors:
        raise CorpusError("reference corpus failed validation:\n  " + "\n  ".join(errors))


def kernel_usable_rates(c: Corpus) -> list[dict]:
    """Rates a calculation kernel may read: human-verified only. Today: none."""
    return [r for r in c.tables.get("rate", []) if r["status"] == "VERIFIED"]
