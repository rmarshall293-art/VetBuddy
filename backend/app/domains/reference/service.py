"""Read-only queries over the `ref` schema for the public (Mode A) API.

Every response carries: the record status on each row, the governance
standard disclaimer, and — for any directory answer — the crisis floor,
re-injected first so it can never be filtered away (T0-08). Jurisdiction
answers carry the unverified-jurisdiction disclaimer. Nothing here returns
an eligibility outcome: leads are labelled leads.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.domains.reference import claims_boundary
from app.platform.crisis_floor import load_crisis_contacts
from app.platform.jurisdiction_status import labelled

_GUARD_JSON = Path(__file__).resolve().parents[4] / "data" / "reference" / "guard_reserve.json"

LEAD_LABEL = "Lead to verify, not a determination. VetBuddy does not decide eligibility."


class UnknownJurisdiction(LookupError):
    pass


class UnknownCareType(LookupError):
    pass


class UnknownRatingCode(LookupError):
    pass


CFR_REFERENCE_LABEL = ("This is VA's published regulation, shown for reference. It explains how VA describes "
                       "criteria; it is not an assessment of your condition.")


def _rows(conn, sql: str, params=()) -> list[dict]:
    return [r["j"] for r in conn.query(f"SELECT to_jsonb(t) AS j FROM ({sql}) t", list(params))]


def _jurisdiction(conn, code: str) -> dict:
    row = conn.one("SELECT code, name, kind, verification_status FROM public.jurisdiction WHERE code = $1", [code])
    if not row:
        raise UnknownJurisdiction(code)
    return labelled(row)


def notice() -> str:
    return claims_boundary.required_text("standard_disclaimer")


def overview(conn) -> dict:
    datasets = _rows(conn, "SELECT dataset_id, title, version, as_of, review_by, record_count, sha256 "
                           "FROM ref.dataset ORDER BY dataset_id")
    posture = _rows(conn, "SELECT tbl AS table, status, count FROM ref.v_status_posture ORDER BY 1, 2")
    cov = conn.one("SELECT count(*) FILTER (WHERE directory_entries > 0) AS with_directory, "
                   "count(*) FILTER (WHERE benefit_leads > 0) AS with_benefit_leads, "
                   "count(*) FILTER (WHERE has_financial_summary) AS with_financial_summary, "
                   "count(*) FILTER (WHERE verification_status = 'verified') AS verified, "
                   "count(*) AS jurisdictions FROM ref.v_coverage")
    verified = conn.one("SELECT (SELECT count(*) FROM ref.rate WHERE status = 'VERIFIED') + "
                        "(SELECT count(*) FROM ref.directory_entry WHERE status = 'VERIFIED') + "
                        "(SELECT count(*) FROM ref.timeline_window WHERE status = 'VERIFIED') + "
                        "(SELECT count(*) FROM ref.rating_code WHERE status = 'VERIFIED') AS n")["n"]
    return {"datasets": datasets, "status_posture": posture, "coverage": cov,
            "records_verified_by_a_named_human": verified,
            "consequence": ("Reference data is context and leads only. No rule is verified (G1), so no benefit "
                            "answer is assertive and every jurisdiction shows its disclaimer."),
            "notice": notice()}


def women_veterans(conn, jurisdiction: str | None, care_type: str | None) -> dict:
    code = (jurisdiction or "FEDERAL").upper()
    jur = _jurisdiction(conn, code)
    if care_type:
        if not conn.one("SELECT 1 AS ok FROM ref.care_type WHERE code = $1", [care_type]):
            raise UnknownCareType(care_type)
    cols = ("entry_id, kind, jurisdiction_code, name, place, org_type, program, care_types, phone, text_line, "
            "mailbox, url, eligibility_note, caveat, dedicated_coordinator, last_checked, status, source_ids")
    where = "jurisdiction_code IN ('FEDERAL', $1)"
    params: list = [code]
    if care_type:
        where += " AND $2 = ANY(care_types)"
        params.append(care_type)
    entries = _rows(conn, f"SELECT {cols} FROM ref.directory_entry WHERE {where} "
                          "ORDER BY CASE kind WHEN 'state_office' THEN 0 WHEN 'territory_dv_coalition' THEN 1 "
                          "WHEN 'national' THEN 2 WHEN 'facility_role' THEN 3 ELSE 4 END, name, place", params)
    local = [e for e in entries if e["jurisdiction_code"] == code and code != "FEDERAL"]
    return {
        "crisis_contacts": load_crisis_contacts(),
        "jurisdiction": jur,
        "care_type": care_type,
        "count": len(entries),
        "local_count": len(local),
        "coverage_note": (None if local or code == "FEDERAL" else
                          "No local records for this jurisdiction yet. That means we have no data for your area, "
                          "not that there is nothing in your area."),
        "entries": entries,
        "notice": notice(),
    }


def jurisdiction_profile(conn, code: str) -> dict:
    code = code.upper()
    jur = _jurisdiction(conn, code)
    summary = _rows(conn, "SELECT military_retirement_tax, no_state_income_tax, disabled_veteran_property_tax, "
                          "notable_programs, status, source_ids FROM ref.state_summary WHERE jurisdiction_code = $1", [code])
    leads = _rows(conn, "SELECT lead_id, category, text, authority, note, conflict_id, status, source_ids "
                        "FROM ref.benefit_lead WHERE jurisdiction_code = $1 ORDER BY category, lead_id", [code])
    stats = _rows(conn, "SELECT stat_id, metric, value, unit, period, note, conflict_id, status, source_ids "
                        "FROM ref.statistic WHERE jurisdiction_code = $1 ORDER BY metric, stat_id", [code])
    conflict_ids = sorted({x["conflict_id"] for x in leads + stats if x.get("conflict_id")})
    conflicts = _rows(conn, "SELECT conflict_id, subject, status, readings, why_it_matters, next_action "
                            "FROM ref.conflict WHERE conflict_id = ANY($1::text[]) ORDER BY conflict_id",
                      [conflict_ids]) if conflict_ids else []
    return {"jurisdiction": jur, "financial_summary": summary[0] if summary else None, "benefit_leads": leads,
            "lead_label": LEAD_LABEL, "statistics": stats, "conflicts": conflicts, "notice": notice()}


def conflicts(conn) -> dict:
    return {"conflicts": _rows(conn, "SELECT conflict_id, subject, status, readings, why_it_matters, next_action, "
                                     "resolution, blocking_for FROM ref.conflict ORDER BY conflict_id"),
            "supersessions": _rows(conn, "SELECT supersession_id, old_value, new_value, effective, note "
                                         "FROM ref.supersession ORDER BY supersession_id")}


def rating_schedule(conn, body_system: str | None) -> dict:
    """Code index (no criteria text). Search is by body system only: there is
    deliberately no symptom lookup (governance section 5)."""
    where, params = ("WHERE body_system = $1", [body_system]) if body_system else ("", [])
    codes = _rows(conn, "SELECT code, name, body_system, subsection, cfr_section, has_criteria, status, status_note "
                        f"FROM ref.rating_code {where} ORDER BY code", params)
    systems = _rows(conn, "SELECT body_system, count(*) AS codes FROM ref.rating_code GROUP BY 1 ORDER BY 1")
    return {"codes": codes, "body_systems": systems, "label": CFR_REFERENCE_LABEL, "notice": notice(),
            "vso_referral": claims_boundary.required_text("vso_referral_block")}


def rating_code(conn, code: str) -> dict:
    rows = _rows(conn, "SELECT * FROM ref.rating_code WHERE code = $1", [code])
    if not rows:
        raise UnknownRatingCode(code)
    criteria = _rows(conn, "SELECT percent, criteria_text FROM ref.rating_criterion WHERE code = $1 ORDER BY position", [code])
    return {"code": rows[0], "criteria": criteria, "label": CFR_REFERENCE_LABEL, "notice": notice(),
            "vso_referral": claims_boundary.required_text("vso_referral_block")}


@lru_cache(maxsize=1)
def _guard_enums() -> dict:
    d = json.loads(_GUARD_JSON.read_text())
    return {"components": d["components"], "statuses": d["statuses"], "governing_rule": d["governing_rule"],
            "tier_caveat_text": d["tier_caveat_text"], "review_cadence": d["review_cadence"]}


def guard_reserve(conn) -> dict:
    return {**_guard_enums(),
            "authorities": _rows(conn, "SELECT authority_id, citation, label, qualifies_ch33, tier_caveat, guard_only, "
                                       "coast_guard_only, status FROM ref.duty_authority ORDER BY authority_id::text COLLATE \"C\""),
            "rule_leads": _rows(conn, "SELECT lead_id, benefit, citation, lead, caveat, status FROM ref.rule_lead "
                                      "WHERE domain = 'guard_reserve' ORDER BY lead_id"),
            "lead_label": LEAD_LABEL, "notice": notice()}
