"""
Deterministic Mission Router (master spec §3, §4; v4.0 §18).

Pure function: same RouterInput + same `today` -> byte-identical output.
No model call, no database, no clock read (the caller passes `today`).
The output is the factual skeleton of the Mission Brief; any AI narration
added later may only explain it, never change it.

Unknown facts are never filled with guesses: an unknown separation date
yields stage "unknown" plus a task to confirm it; an unknown Guard/Reserve
authority yields a task to read it off the orders.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass, asdict, field

from .task_library import GOAL_LANES, GOAL_TEMPLATES, TEMPLATES

ROUTER_POLICY_VERSION = "mission-router.v0.1.0"

PERSONAS = ("service_member", "veteran", "guard_reserve", "spouse_family", "caregiver", "survivor")
COMPONENTS = ("active_duty", "national_guard", "reserve", "retired", "retired_reserve_gray_area",
              "separated", "medically_separated")
AUTHORITIES = ("title_10", "title_32", "state_active_duty", "idt_annual_training", "not_applicable", "unknown")
BRANCHES = ("Army", "Navy", "Marine Corps", "Air Force", "Space Force", "Coast Guard")
GOALS = tuple(GOAL_LANES.keys())
URGENCIES = ("immediate", "7_days", "30_days", "90_days", "long_term", "info_only")
DIMENSIONS = ("documents", "benefits", "claims_evidence", "coverage", "career", "education",
              "financial", "housing_relocation", "family", "community")

STAGE_LABELS = {
    "in_service": "In-service readiness (more than 24 months out)",
    "t_24_12m": "24 to 12 months before separation",
    "t_12_6m": "12 to 6 months before separation",
    "t_180_90d": "180 to 90 days before separation",
    "t_90_30d": "90 to 30 days before separation",
    "t_30d_sep": "Final 30 days before separation",
    "day_0_30": "First 30 days after separation",
    "day_31_90": "Days 31 to 90 after separation",
    "month_3_12": "Months 3 to 12 after separation",
    "year_1_2": "Year 1 to 2 after separation",
    "year_2_3": "Year 2 to 3 after separation",
    "year_3_5": "Year 3 to 5 after separation",
    "ongoing": "Ongoing veteran life (more than 5 years)",
    "unknown": "Not yet known — separation date not provided",
}


NOTICE_TEXT = {
    "BENEFIT_SCREENING_NOT_AVAILABLE": "VetBuddy does not show benefit matches yet. No eligibility rule has completed "
                                       "primary-source verification by a named reviewer, and VetBuddy will not guess.",
    "STAGE_UNKNOWN": "Your transition stage is unknown because no separation date was given.",
    "AUTHORITY_UNKNOWN": "Guard/Reserve authority is unknown. Nothing has been assumed about Title 10 or Title 32 service.",
}


@dataclass(frozen=True)
class RouterInput:
    persona: str
    branch: str
    component: str
    legal_authority: str | None
    separation_date: dt.date | None
    current_jurisdiction: str
    destination_jurisdiction: str | None
    goals: tuple[str, ...]
    urgency: str

    def canonical(self) -> dict:
        d = asdict(self)
        d["separation_date"] = self.separation_date.isoformat() if self.separation_date else None
        d["goals"] = sorted(set(self.goals))
        return d

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.canonical(), sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class PlannedTask:
    template_id: str
    lane: str
    dimension: str
    title: str
    why: str
    priority: int
    confirm_with: str | None


@dataclass
class RouterOutput:
    policy_version: str
    input_hash: str
    stage: str
    stage_label: str
    days_to_separation: int | None
    track: str
    lanes: list[str]
    tasks: list[PlannedTask]
    notices: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class RouterInputError(ValueError):
    def __init__(self, field_name: str, message: str):
        super().__init__(f"{field_name}: {message}")
        self.field = field_name


def validate(inp: RouterInput, known_jurisdictions: set[str]) -> None:
    def need(cond: bool, f: str, msg: str) -> None:
        if not cond:
            raise RouterInputError(f, msg)
    need(inp.persona in PERSONAS, "persona", f"must be one of {PERSONAS}")
    need(inp.branch in BRANCHES, "branch", f"must be one of {BRANCHES}")
    need(inp.component in COMPONENTS, "component", f"must be one of {COMPONENTS}")
    need(inp.legal_authority is None or inp.legal_authority in AUTHORITIES, "legal_authority",
         f"must be one of {AUTHORITIES}")
    need(not (inp.component in ("national_guard", "reserve") and inp.legal_authority is None), "legal_authority",
         "is required for National Guard and Reserve (choose 'unknown' if you do not have your orders)")
    need(inp.current_jurisdiction in known_jurisdictions, "current_jurisdiction", "unknown jurisdiction code")
    need(inp.destination_jurisdiction is None or inp.destination_jurisdiction in known_jurisdictions,
         "destination_jurisdiction", "unknown jurisdiction code")
    need(all(g in GOALS for g in inp.goals), "goals", f"each goal must be one of {GOALS}")
    need(inp.urgency in URGENCIES, "urgency", f"must be one of {URGENCIES}")


def compute_stage(separation_date: dt.date | None, today: dt.date) -> tuple[str, int | None]:
    if separation_date is None:
        return "unknown", None
    d = (separation_date - today).days          # positive = still in service
    if d > 730: return "in_service", d
    if d > 365: return "t_24_12m", d
    if d > 180: return "t_12_6m", d
    if d > 90:  return "t_180_90d", d
    if d > 30:  return "t_90_30d", d
    if d >= 0:  return "t_30d_sep", d
    after = -d
    if after <= 30:   return "day_0_30", d
    if after <= 90:   return "day_31_90", d
    if after <= 365:  return "month_3_12", d
    if after <= 730:  return "year_1_2", d
    if after <= 1095: return "year_2_3", d
    if after <= 1825: return "year_3_5", d
    return "ongoing", d


def compute_track(inp: RouterInput) -> str:
    if inp.persona in ("spouse_family", "caregiver", "survivor"):
        return "spouse_family"
    if inp.component == "medically_separated":
        return "medical_separation"
    if inp.component in ("national_guard", "reserve", "retired_reserve_gray_area"):
        return "guard_reserve"
    if inp.component == "retired":
        return "retirement"
    if inp.destination_jurisdiction and inp.destination_jurisdiction != inp.current_jurisdiction:
        return "pcs" if inp.component == "active_duty" else "re_entry"
    return "ets_eas" if inp.component == "active_duty" else "re_entry"


def route(inp: RouterInput, today: dt.date) -> RouterOutput:
    stage, days = compute_stage(inp.separation_date, today)
    track = compute_track(inp)
    relocating = bool(inp.destination_jurisdiction and inp.destination_jurisdiction != inp.current_jurisdiction)

    chosen: list[str] = ["DOC-01"]
    if stage == "unknown" and inp.persona in ("service_member", "guard_reserve", "veteran"):
        chosen.append("FACT-DATE")
    if inp.component in ("national_guard", "reserve"):
        if inp.legal_authority == "unknown":
            chosen.append("GR-AUTH")
        chosen.append("GR-RECORD")
    if inp.component in ("active_duty", "national_guard", "reserve") and (stage in TEMPLATES["TAP-01"].stages):
        chosen.append("TAP-01")
    if inp.component == "medically_separated":
        chosen.append("MED-01")
    if stage in TEMPLATES["COV-01"].stages:
        chosen.append("COV-01")
    for g in sorted(set(inp.goals)):
        chosen.extend(GOAL_TEMPLATES[g])
    if relocating:
        chosen.extend(["REL-01", "HOU-01"])

    seen: set[str] = set()
    tasks: list[PlannedTask] = []
    for tid in chosen:
        if tid in seen:
            continue
        seen.add(tid)
        t = TEMPLATES[tid]
        if t.stages and stage not in t.stages:
            continue
        tasks.append(PlannedTask(t.template_id, t.lane, t.dimension, t.title, t.why, t.priority, t.confirm_with))
    tasks.sort(key=lambda t: (t.priority, t.template_id))

    lanes: list[str] = []
    for lane in [GOAL_LANES[g] for g in sorted(set(inp.goals))] + [t.lane for t in tasks]:
        if lane != "other" and lane not in lanes:
            lanes.append(lane)
    if inp.component in ("national_guard", "reserve", "retired_reserve_gray_area") and "guard_reserve" not in lanes:
        lanes.append("guard_reserve")
    if relocating and "state_local" not in lanes:
        lanes.append("state_local")
    if not lanes:
        lanes.append("benefits")

    notices: list[dict] = [{"code": "BENEFIT_SCREENING_NOT_AVAILABLE",
                             "message": NOTICE_TEXT["BENEFIT_SCREENING_NOT_AVAILABLE"]}]
    if stage == "unknown":
        notices.append({"code": "STAGE_UNKNOWN", "message": NOTICE_TEXT["STAGE_UNKNOWN"]})
    if inp.legal_authority == "unknown":
        notices.append({"code": "AUTHORITY_UNKNOWN", "message": NOTICE_TEXT["AUTHORITY_UNKNOWN"]})

    return RouterOutput(
        policy_version=ROUTER_POLICY_VERSION,
        input_hash=inp.digest(),
        stage=stage,
        stage_label=STAGE_LABELS[stage],
        days_to_separation=days,
        track=track,
        lanes=lanes,
        tasks=tasks,
        notices=notices,
    )


def readiness(task_rows: list[dict]) -> list[dict]:
    """Transparent per-dimension status — explicitly NOT a score."""
    out = []
    for dim in DIMENSIONS:
        ts = [t for t in task_rows if t.get("readiness_dimension") == dim and t.get("status") != "cancelled"]
        done = sum(1 for t in ts if t.get("status") == "done")
        if not ts:
            status = "not_assessed"
        elif done == len(ts):
            status = "ready"
        elif done or any(t.get("status") == "in_progress" for t in ts):
            status = "in_progress"
        else:
            status = "not_started"
        out.append({"dimension": dim, "status": status, "done": done, "total": len(ts)})
    return out
