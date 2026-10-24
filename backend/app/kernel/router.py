"""Deterministic Mission Router: declared facts + today -> stage, lanes, tasks.

Pure: no I/O, no clock reads (callers inject `today`), no model. The same
input and date always produce byte-identical output (invariant I1). The browser
kernel in frontend/src/kernel.js mirrors this function; tests/test_parity.py
proves they agree on shared golden fixtures.

Unknown facts stay unknown (R7 / T0-07): a missing separation date yields stage
"unknown" plus a task to find it, never a guessed stage.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date

from . import vocab
from .jurisdictions import JURISDICTION_CODES

GUARD_RESERVE = ("national_guard", "reserve")
GUARD_RESERVE_ALL = ("national_guard", "reserve", "retired_reserve_gray_area")
FAMILY_PERSONAS = ("spouse_family", "caregiver", "survivor")
SERVICE_PERSONAS = ("service_member", "guard_reserve", "veteran")


class RouterInputError(ValueError):
    def __init__(self, field_name: str, message: str):
        super().__init__(f"{field_name}: {message}")
        self.field = field_name


@dataclass(frozen=True)
class RouterInput:
    persona: str
    branch: str
    component: str
    current_jurisdiction: str
    urgency: str = "30_days"
    goals: tuple[str, ...] = field(default_factory=tuple)
    legal_authority: str | None = None
    separation_date: date | None = None
    destination_jurisdiction: str | None = None

    def canonical(self) -> dict:
        return {
            "branch": self.branch,
            "component": self.component,
            "current_jurisdiction": self.current_jurisdiction,
            "destination_jurisdiction": self.destination_jurisdiction,
            "goals": sorted(set(self.goals)),
            "legal_authority": self.legal_authority,
            "persona": self.persona,
            "separation_date": self.separation_date.isoformat() if self.separation_date else None,
            "urgency": self.urgency,
        }

    def input_hash(self) -> str:
        return hashlib.sha256(json.dumps(self.canonical(), sort_keys=True).encode()).hexdigest()


def validate(inp: RouterInput) -> None:
    def need(cond: bool, f: str, msg: str) -> None:
        if not cond:
            raise RouterInputError(f, msg)

    need(inp.persona in vocab.PERSONAS, "persona", "choose who you are")
    need(inp.branch in vocab.BRANCHES, "branch", "choose a branch")
    need(inp.component in vocab.COMPONENTS, "component", "choose a status")
    need(inp.legal_authority is None or inp.legal_authority in vocab.AUTHORITIES, "legal_authority", "unknown value")
    need(
        not (inp.component in GUARD_RESERVE and inp.legal_authority is None),
        "legal_authority",
        "is required for National Guard and Reserve (choose 'unknown' if you do not have your orders)",
    )
    need(inp.current_jurisdiction in JURISDICTION_CODES, "current_jurisdiction", "choose where you live")
    need(
        inp.destination_jurisdiction is None or inp.destination_jurisdiction in JURISDICTION_CODES,
        "destination_jurisdiction",
        "unknown jurisdiction",
    )
    need(all(g in vocab.GOALS for g in inp.goals), "goals", "unknown goal")
    need(inp.urgency in vocab.URGENCIES, "urgency", "unknown urgency")


def compute_stage(separation_date: date | None, today: date) -> tuple[str, int | None]:
    if separation_date is None:
        return "unknown", None
    d = (separation_date - today).days
    if d > 730:
        return "in_service", d
    if d > 365:
        return "t_24_12m", d
    if d > 180:
        return "t_12_6m", d
    if d > 90:
        return "t_180_90d", d
    if d > 30:
        return "t_90_30d", d
    if d >= 0:
        return "t_30d_sep", d
    a = -d
    for limit, stage in ((30, "day_0_30"), (90, "day_31_90"), (365, "month_3_12"),
                         (730, "year_1_2"), (1095, "year_2_3"), (1825, "year_3_5")):
        if a <= limit:
            return stage, d
    return "ongoing", d


def compute_track(inp: RouterInput) -> str:
    if inp.persona in FAMILY_PERSONAS:
        return "spouse_family"
    if inp.component == "medically_separated":
        return "medical_separation"
    if inp.component in GUARD_RESERVE_ALL:
        return "guard_reserve"
    if inp.component == "retired":
        return "retirement"
    if inp.destination_jurisdiction and inp.destination_jurisdiction != inp.current_jurisdiction:
        return "pcs" if inp.component == "active_duty" else "re_entry"
    return "ets_eas" if inp.component == "active_duty" else "re_entry"


def route(inp: RouterInput, today: date) -> dict:
    """Return the Mission Brief skeleton. Raises RouterInputError on bad input."""
    validate(inp)
    stage, days = compute_stage(inp.separation_date, today)
    track = compute_track(inp)
    relocating = bool(inp.destination_jurisdiction and inp.destination_jurisdiction != inp.current_jurisdiction)
    T = vocab.TEMPLATES
    goals = sorted(set(inp.goals))

    chosen = ["DOC-01"]
    if stage == "unknown" and inp.persona in SERVICE_PERSONAS:
        chosen.append("FACT-DATE")
    if inp.component in GUARD_RESERVE:
        if inp.legal_authority == "unknown":
            chosen.append("GR-AUTH")
        chosen.append("GR-RECORD")
    if inp.component in ("active_duty", *GUARD_RESERVE) and stage in T["TAP-01"]["stages"]:
        chosen.append("TAP-01")
    if inp.component == "medically_separated":
        chosen.append("MED-01")
    if stage in T["COV-01"]["stages"]:
        chosen.append("COV-01")
    for g in goals:
        chosen.extend(vocab.GOAL_TEMPLATES[g])
    if relocating:
        chosen.extend(["REL-01", "HOU-01"])

    seen: set[str] = set()
    tasks = []
    for tid in chosen:
        if tid in seen:
            continue
        seen.add(tid)
        t = T[tid]
        if t["stages"] and stage not in t["stages"]:
            continue
        tasks.append({
            "template_id": tid, "lane": t["lane"], "dimension": t["dimension"], "title": t["title"],
            "why": t["why"], "priority": t["priority"], "confirm_with": t["confirm_with"],
        })
    tasks.sort(key=lambda t: (t["priority"], t["template_id"]))

    lanes: list[str] = []
    for lane in [vocab.GOAL_LANES[g] for g in goals] + [t["lane"] for t in tasks]:
        if lane != "other" and lane not in lanes:
            lanes.append(lane)
    if inp.component in GUARD_RESERVE_ALL and "guard_reserve" not in lanes:
        lanes.append("guard_reserve")
    if relocating and "state_local" not in lanes:
        lanes.append("state_local")
    if not lanes:
        lanes.append("benefits")

    notices = [{"code": "BENEFIT_SCREENING_NOT_AVAILABLE", "message": vocab.NOTICE_TEXT["BENEFIT_SCREENING_NOT_AVAILABLE"]}]
    if stage == "unknown":
        notices.append({"code": "STAGE_UNKNOWN", "message": vocab.NOTICE_TEXT["STAGE_UNKNOWN"]})
    if inp.legal_authority == "unknown":
        notices.append({"code": "AUTHORITY_UNKNOWN", "message": vocab.NOTICE_TEXT["AUTHORITY_UNKNOWN"]})

    return {
        "policy_version": vocab.ROUTER_POLICY_VERSION,
        "input_hash": inp.input_hash(),
        "stage": stage,
        "stage_label": vocab.STAGE_LABELS[stage],
        "days_to_separation": days,
        "track": track,
        "lanes": lanes,
        "tasks": tasks,
        "notices": notices,
    }


def readiness(rows: list[dict]) -> list[dict]:
    """Per-dimension progress from task rows ({readiness_dimension, status}). Not a score."""
    out = []
    for dim in vocab.DIMENSIONS:
        ts = [t for t in rows if t["readiness_dimension"] == dim and t["status"] != "cancelled"]
        done = sum(1 for t in ts if t["status"] == "done")
        if not ts:
            status = "not_assessed"
        elif done == len(ts):
            status = "ready"
        elif done or any(t["status"] == "in_progress" for t in ts):
            status = "in_progress"
        else:
            status = "not_started"
        out.append({"dimension": dim, "status": status, "done": done, "total": len(ts)})
    return out
