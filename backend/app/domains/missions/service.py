"""Mission & Work OS service for slice 01.

Every function takes an open tenant-scoped Connection (RLS context already
set by the API layer) and a Principal. Ownership is enforced twice:
RLS (tenant) in Postgres, and person/user ownership in SQL predicates here.
Rows the caller cannot see are reported as NOT FOUND, never FORBIDDEN, so
IDs cannot be enumerated across tenants.
"""
from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from app.domains.missions import router_policy as rp
from app.domains.trust import audit, consent
from app.domains.trust.auth import Principal
from app.infra.db import Connection
from app.platform.jurisdiction_status import labelled

SERVICE_PERSONAS = ("service_member", "veteran", "guard_reserve")
ALLOWED_TRANSITIONS = {
    "todo": {"in_progress", "done", "blocked", "cancelled"},
    "in_progress": {"todo", "done", "blocked", "cancelled"},
    "blocked": {"todo", "in_progress", "cancelled"},
    "done": {"todo"},
    "cancelled": {"todo"},
}


class NotFound(Exception):
    pass


class Conflict(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def known_jurisdictions(conn: Connection) -> dict[str, dict]:
    return {r["code"]: r for r in conn.query(
        "SELECT jurisdiction_id, code, name, kind, verification_status FROM jurisdiction")}


def _emit(conn: Connection, p: Principal, event_type: str, agg_type: str, agg_id: uuid.UUID,
          payload: dict, correlation_id: str) -> None:
    conn.query(
        "INSERT INTO outbox_event (tenant_id, event_type, aggregate_type, aggregate_id, actor_user_id,"
        " correlation_id, idempotency_key, payload) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
        [p.tenant_id, event_type, agg_type, agg_id, p.user_id, correlation_id,
         f"{event_type}:{agg_id}:{correlation_id}", payload])


def _me(conn: Connection, p: Principal) -> dict:
    u = conn.one("SELECT user_id, privacy_mode, role FROM app_user WHERE user_id = $1 AND deleted_at IS NULL",
                 [p.user_id])
    if u is None:
        raise NotFound("user")
    return u


# ── identity (dev) ───────────────────────────────────────────────────────────

def create_individual_account(conn: Connection, tenant_id: uuid.UUID) -> uuid.UUID:
    """Caller has already set the RLS context to `tenant_id`."""
    conn.query("INSERT INTO tenant (tenant_id, name, kind) VALUES ($1, $2, 'individual')",
               [tenant_id, "individual"])
    user = conn.one("INSERT INTO app_user (tenant_id, privacy_mode) VALUES ($1, 'B') RETURNING user_id", [tenant_id])
    audit.record(conn, tenant_id, user["user_id"], "ACCOUNT_CREATED", "app_user", user["user_id"],
                 {"privacy_mode": "B", "auth_method": "dev_mock"})
    return user["user_id"]


def get_me(conn: Connection, p: Principal) -> dict:
    u = _me(conn, p)
    c = consent.active_consent(conn, p.user_id, consent.MISSION_PURPOSE)
    return {"user_id": str(u["user_id"]), "privacy_mode": u["privacy_mode"], "auth_method": p.auth_method,
            "mission_consent": bool(c)}


def set_privacy_mode(conn: Connection, p: Principal, mode: str, mode_c_enabled: bool, corr: str) -> dict:
    if mode not in ("A", "B", "C"):
        raise Conflict("INVALID_MODE", "privacy mode must be A, B or C")
    if mode == "C" and not mode_c_enabled:
        raise Conflict("MODE_C_DISABLED",
                       "Managed-case mode (C) is disabled until its security review and tests pass.")
    u = _me(conn, p)
    if mode == "A":
        raise Conflict("MODE_A_IS_GUEST",
                       "Mode A is guest-only. Use the guest preview without signing in; to stop storing data, "
                       "revoke consent.")
    conn.query("UPDATE app_user SET privacy_mode = $1 WHERE user_id = $2", [mode, p.user_id])
    audit.record(conn, p.tenant_id, p.user_id, "PRIVACY_MODE_CHANGED", "app_user", p.user_id,
                 {"from": u["privacy_mode"], "to": mode})
    return {"privacy_mode": mode}


# ── consent ──────────────────────────────────────────────────────────────────

def grant_consent(conn: Connection, p: Principal, purpose: str, corr: str) -> dict:
    _me(conn, p)
    purp = conn.one("SELECT purpose, data_classes FROM consent_purpose WHERE purpose = $1 AND allowed", [purpose])
    if purp is None:
        raise Conflict("PURPOSE_NOT_ALLOWED", "That consent purpose is not offered.")
    existing = consent.active_consent(conn, p.user_id, purpose)
    if existing:
        return {"consent_id": str(existing["consent_id"]), "purpose": purpose, "status": "active"}
    row = conn.one("INSERT INTO consent_record (tenant_id, user_id, purpose, data_categories)"
                   " VALUES ($1,$2,$3,$4) RETURNING consent_id",
                   [p.tenant_id, p.user_id, purpose, purp["data_classes"]])
    audit.record(conn, p.tenant_id, p.user_id, "CONSENT_GRANTED", "consent_record", row["consent_id"],
                 {"purpose": purpose})
    _emit(conn, p, "CONSENT_UPDATED", "consent_record", row["consent_id"], {"purpose": purpose, "state": "granted"}, corr)
    return {"consent_id": str(row["consent_id"]), "purpose": purpose, "status": "active"}


def list_consents(conn: Connection, p: Principal) -> list[dict]:
    rows = conn.query(
        "SELECT c.consent_id, c.purpose, c.granted_at, c.revoked_at, cp.description FROM consent_record c"
        " JOIN consent_purpose cp USING (purpose) WHERE c.user_id = $1 ORDER BY c.granted_at DESC", [p.user_id])
    return [{"consent_id": str(r["consent_id"]), "purpose": r["purpose"], "description": r["description"],
             "granted_at": r["granted_at"].isoformat(), "revoked_at": r["revoked_at"].isoformat() if r["revoked_at"] else None,
             "status": "revoked" if r["revoked_at"] else "active"} for r in rows]


def revoke_consent(conn: Connection, p: Principal, consent_id: uuid.UUID, corr: str) -> dict:
    row = conn.one("UPDATE consent_record SET revoked_at = now() WHERE consent_id = $1 AND user_id = $2"
                   " AND revoked_at IS NULL RETURNING consent_id, purpose", [consent_id, p.user_id])
    if row is None:
        raise NotFound("consent")
    audit.record(conn, p.tenant_id, p.user_id, "CONSENT_REVOKED", "consent_record", consent_id,
                 {"purpose": row["purpose"]})
    _emit(conn, p, "CONSENT_UPDATED", "consent_record", consent_id, {"purpose": row["purpose"], "state": "revoked"}, corr)
    return {"consent_id": str(consent_id), "status": "revoked"}


# ── onboarding → mission ─────────────────────────────────────────────────────

def preview(inp: rp.RouterInput, jur: dict[str, dict], today: dt.date) -> dict:
    """Privacy Mode A: compute, return, persist nothing."""
    rp.validate(inp, set(jur))
    out = rp.route(inp, today)
    tasks = [dict(t.__dict__, status="todo") for t in out.tasks]
    return _brief_payload(out, inp, tasks, jur, mission_id=None, persisted=False, today=today)


def onboard(conn: Connection, p: Principal, inp: rp.RouterInput, display_name: str | None,
            consent_given: bool, today: dt.date, corr: str) -> dict:
    jur = known_jurisdictions(conn)
    rp.validate(inp, set(jur))
    me = _me(conn, p)
    if me["privacy_mode"] != "B":
        raise Conflict("MODE_NOT_SUPPORTED", "Only personal private mode (B) can save a mission in this version.")
    if not consent_given and consent.active_consent(conn, p.user_id, consent.MISSION_PURPOSE) is None:
        raise consent.ConsentRequired(consent.MISSION_PURPOSE)
    if consent_given:
        grant_consent(conn, p, consent.MISSION_PURPOSE, corr)

    out = rp.route(inp, today)
    cur = jur[inp.current_jurisdiction]
    dest = jur.get(inp.destination_jurisdiction) if inp.destination_jurisdiction else None

    person = conn.one("INSERT INTO person_profile (tenant_id, user_id, relationship, display_name, state_territory)"
                      " VALUES ($1,$2,'self',$3,$4) RETURNING person_id",
                      [p.tenant_id, p.user_id, display_name, inp.current_jurisdiction])["person_id"]
    if inp.persona in SERVICE_PERSONAS:
        conn.query("INSERT INTO service_record (tenant_id, person_id, branch, component, legal_authority, service_end,"
                   " fact_status) VALUES ($1,$2,$3,$4,$5,$6,'DECLARED')",
                   [p.tenant_id, person, inp.branch, inp.component, inp.legal_authority, inp.separation_date])
    conn.query("INSERT INTO transition_context (tenant_id, person_id, track, stage, separation_date,"
               " current_jurisdiction_id, destination_jurisdiction_id) VALUES ($1,$2,$3,$4,$5,$6,$7)",
               [p.tenant_id, person, out.track, out.stage, inp.separation_date, cur["jurisdiction_id"],
                dest["jurisdiction_id"] if dest else None])

    mission = conn.one(
        "INSERT INTO mission (tenant_id, person_id, title, primary_lane, urgency, router_policy_version, goals,"
        " router_input, router_input_hash, brief) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING mission_id",
        [p.tenant_id, person, "My transition mission", out.lanes[0], inp.urgency, out.policy_version,
         sorted(set(inp.goals)), inp.canonical(), out.input_hash,
         {k: v for k, v in out.to_dict().items() if k != "tasks"}])["mission_id"]
    _emit(conn, p, "MISSION_CREATED", "mission", mission, {"policy_version": out.policy_version}, corr)

    cases: dict[str, uuid.UUID] = {}
    for lane in out.lanes + sorted({t.lane for t in out.tasks} - set(out.lanes)):
        cid = conn.one("INSERT INTO crm_case (tenant_id, mission_id, lane, owner_user_id) VALUES ($1,$2,$3,$4)"
                       " RETURNING case_id", [p.tenant_id, mission, lane, p.user_id])["case_id"]
        cases[lane] = cid
        _emit(conn, p, "CASE_CREATED", "crm_case", cid, {"lane": lane}, corr)
    for t in out.tasks:
        tid = conn.one(
            "INSERT INTO task (tenant_id, case_id, title, description, priority, assigned_user_id, ai_generated,"
            " template_id, readiness_dimension) VALUES ($1,$2,$3,$4,$5,$6,false,$7,$8) RETURNING task_id",
            [p.tenant_id, cases[t.lane], t.title, t.why, t.priority, p.user_id, t.template_id, t.dimension])["task_id"]
        _emit(conn, p, "TASK_CREATED", "task", tid, {"template_id": t.template_id}, corr)

    _emit(conn, p, "PROFILE_COMPLETED", "person_profile", person, {"persona": inp.persona}, corr)
    audit.record(conn, p.tenant_id, p.user_id, "MISSION_CREATED", "mission", mission,
                 {"policy_version": out.policy_version, "input_hash": out.input_hash,
                  "lanes": out.lanes, "task_count": len(out.tasks)})
    return {"mission_id": str(mission)}


def list_missions(conn: Connection, p: Principal) -> list[dict]:
    consent.require(conn, p.user_id)
    rows = conn.query(
        "SELECT m.mission_id, m.title, m.status, m.created_at FROM mission m JOIN person_profile pp USING (person_id)"
        " WHERE pp.user_id = $1 ORDER BY m.created_at DESC", [p.user_id])
    return [{"mission_id": str(r["mission_id"]), "title": r["title"], "status": r["status"],
             "created_at": r["created_at"].isoformat()} for r in rows]


def _owned_mission(conn: Connection, p: Principal, mission_id: uuid.UUID) -> dict:
    m = conn.one("SELECT m.* FROM mission m JOIN person_profile pp USING (person_id)"
                 " WHERE m.mission_id = $1 AND pp.user_id = $2", [mission_id, p.user_id])
    if m is None:
        raise NotFound("mission")
    return m


def _tasks(conn: Connection, mission_id: uuid.UUID) -> list[dict]:
    return conn.query(
        "SELECT t.task_id, t.title, t.description AS why, t.status, t.priority, t.template_id,"
        " t.readiness_dimension, t.version, t.completed_at, c.lane FROM task t JOIN crm_case c USING (case_id)"
        " WHERE c.mission_id = $1 ORDER BY t.priority, t.template_id", [mission_id])


def _input_from_snapshot(snap: dict) -> rp.RouterInput:
    return rp.RouterInput(
        persona=snap["persona"], branch=snap["branch"], component=snap["component"],
        legal_authority=snap["legal_authority"],
        separation_date=dt.date.fromisoformat(snap["separation_date"]) if snap["separation_date"] else None,
        current_jurisdiction=snap["current_jurisdiction"], destination_jurisdiction=snap["destination_jurisdiction"],
        goals=tuple(snap["goals"]), urgency=snap["urgency"])


def get_brief(conn: Connection, p: Principal, mission_id: uuid.UUID, today: dt.date) -> dict:
    consent.require(conn, p.user_id)
    m = _owned_mission(conn, p, mission_id)
    inp = _input_from_snapshot(m["router_input"])
    jur = known_jurisdictions(conn)
    stored = m["brief"]
    stage_now, days_now = rp.compute_stage(inp.separation_date, today)
    out = rp.RouterOutput(policy_version=m["router_policy_version"], input_hash=m["router_input_hash"],
                          stage=stage_now, stage_label=rp.STAGE_LABELS[stage_now], days_to_separation=days_now,
                          track=stored["track"], lanes=stored["lanes"], tasks=[], notices=stored["notices"])
    tasks = [_task_json(t) for t in _tasks(conn, mission_id)]
    payload = _brief_payload(out, inp, tasks, jur, mission_id=mission_id, persisted=True, today=today)
    if stage_now != stored["stage"]:
        payload["stage_changed_since_created"] = {"from": stored["stage"], "to": stage_now}
    return payload


def _task_json(t: dict) -> dict:
    return {"task_id": str(t["task_id"]), "title": t["title"], "why": t["why"], "status": t["status"],
            "priority": t["priority"], "template_id": t["template_id"], "dimension": t["readiness_dimension"],
            "lane": t["lane"], "version": t["version"],
            "confirm_with": rp.TEMPLATES[t["template_id"]].confirm_with if t["template_id"] in rp.TEMPLATES else None}


def _brief_payload(out: rp.RouterOutput, inp: rp.RouterInput, tasks: list[dict], jur: dict[str, dict],
                   mission_id: uuid.UUID | None, persisted: bool, today: dt.date) -> dict:
    open_tasks = [t for t in tasks if t["status"] not in ("done", "cancelled")]
    rows_for_readiness = [{"readiness_dimension": t["dimension"], "status": t["status"]} for t in tasks]
    js = [labelled(jur[inp.current_jurisdiction])]
    if inp.destination_jurisdiction and inp.destination_jurisdiction != inp.current_jurisdiction:
        js.append(labelled(jur[inp.destination_jurisdiction]))
    return {
        "schema_version": "vetbuddy.mission-brief.v1",
        "mission_id": str(mission_id) if mission_id else None,
        "persisted": persisted,
        "as_of": today.isoformat(),
        "generated_by": "deterministic_router",
        "policy_version": out.policy_version,
        "input_hash": out.input_hash,
        "situation": {
            "persona": inp.persona, "branch": inp.branch, "component": inp.component,
            "legal_authority": inp.legal_authority, "track": out.track,
            "stage": out.stage, "stage_label": out.stage_label, "days_to_separation": out.days_to_separation,
            "facts_status": "DECLARED",
        },
        "goals": sorted(set(inp.goals)),
        "urgency": inp.urgency,
        "lanes": out.lanes,
        "first_five_actions": open_tasks[:5],
        "tasks": tasks,
        "readiness": rp.readiness(rows_for_readiness),
        "jurisdictions": js,
        "benefit_screening": {"status": "DISABLED",
                              "reason": "No eligibility rule is verified yet (gap G1). Matches are withheld, not guessed."},
        "notices": out.notices,
        "limitations": [
            "Everything here is based on facts you declared; none has been verified against your records.",
            "VetBuddy is not a VA-accredited representative and does not file anything for you.",
            "Readiness shows task progress per area. It is not a score and does not predict outcomes.",
        ],
    }


def update_task(conn: Connection, p: Principal, task_id: uuid.UUID, new_status: str, expected_version: int,
                corr: str) -> dict:
    consent.require(conn, p.user_id)
    t = conn.one("SELECT t.task_id, t.status, t.version FROM task t JOIN crm_case c USING (case_id)"
                 " JOIN mission m USING (mission_id) JOIN person_profile pp USING (person_id)"
                 " WHERE t.task_id = $1 AND pp.user_id = $2 FOR UPDATE OF t", [task_id, p.user_id])
    if t is None:
        raise NotFound("task")
    if t["version"] != expected_version:
        raise Conflict("VERSION_CONFLICT", "This task changed since you loaded it. Reload and try again.")
    if new_status == t["status"]:
        return {"task_id": str(task_id), "status": new_status, "version": t["version"]}
    if new_status not in ALLOWED_TRANSITIONS.get(t["status"], set()):
        raise Conflict("INVALID_TRANSITION", f"Cannot move a task from {t['status']} to {new_status}.")
    row = conn.one("UPDATE task SET status = $1, version = version + 1,"
                   " completed_at = CASE WHEN $1 = 'done' THEN now() ELSE NULL END"
                   " WHERE task_id = $2 RETURNING version", [new_status, task_id])
    audit.record(conn, p.tenant_id, p.user_id, "TASK_STATUS_CHANGED", "task", task_id,
                 {"from": t["status"], "to": new_status})
    if new_status == "done":
        _emit(conn, p, "TASK_COMPLETED", "task", task_id, {}, corr)
    return {"task_id": str(task_id), "status": new_status, "version": row["version"]}
