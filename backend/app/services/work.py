"""Work OS service: consent, Master Mission, Master Case, tasks.

Each public function runs inside the caller's scoped transaction, so the domain
change, its audit row and its outbox event commit or roll back together. The
router decides; this module only persists what the router returned.
"""

from __future__ import annotations

import uuid
from datetime import date

import psycopg
from psycopg.types.json import Jsonb

from ..api.errors import ApiError
from ..governance import language
from ..kernel import router as kernel
from ..kernel import vocab
from ..kernel.router import RouterInput

PLAN_STORAGE = "plan_storage"
CONSENT_POLICY_VERSION = "consent-policy.v1.0.0"


def audit(conn: psycopg.Connection, tenant_id: str, actor_id: str, action: str, object_type: str,
          object_id: str | None, trace_id: str, reason_code: str | None = None) -> None:
    conn.execute(
        """INSERT INTO vb.audit_events (tenant_id, actor_kind, actor_id, action, object_type, object_id, reason_code, trace_id)
           VALUES (%s, 'user', %s, %s, %s, %s, %s, %s)""",
        (tenant_id, actor_id, action, object_type, object_id, reason_code, trace_id))


def emit(conn: psycopg.Connection, tenant_id: str, event_type: str, aggregate_type: str, aggregate_id: str,
         trace_id: str, payload: dict | None = None) -> None:
    """Outbox write. Payload carries ids and counts only, never facts."""
    conn.execute(
        """INSERT INTO vb.outbox (tenant_id, event_type, aggregate_type, aggregate_id, idempotency_key, payload, trace_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (tenant_id, event_type, aggregate_type, aggregate_id, f"{aggregate_type}:{aggregate_id}:{event_type}:{trace_id}",
         Jsonb(payload or {}), trace_id))


# ── consent ──────────────────────────────────────────────────────────────────

def active_consents(conn: psycopg.Connection) -> list[dict]:
    return conn.execute(
        "SELECT purpose, granted_at, policy_version FROM vb.consents WHERE revoked_at IS NULL ORDER BY purpose").fetchall()


def grant_consent(conn: psycopg.Connection, tenant_id: str, user_id: str, purpose: str, trace_id: str) -> dict:
    row = conn.execute("SELECT foreclosed FROM vb.consent_purposes WHERE purpose = %s", (purpose,)).fetchone()
    if row is None:
        raise ApiError(422, "UNKNOWN_PURPOSE", "That consent purpose does not exist.")
    if row["foreclosed"]:
        raise ApiError(422, "PURPOSE_FORECLOSED", "VetBuddy never asks for or records consent to this use of your data.")
    existing = conn.execute("SELECT id, purpose, granted_at FROM vb.consents WHERE purpose = %s AND revoked_at IS NULL",
                            (purpose,)).fetchone()
    if existing:
        return {"purpose": purpose, "granted_at": existing["granted_at"], "created": False}
    new = conn.execute(
        """INSERT INTO vb.consents (tenant_id, user_id, purpose, policy_version) VALUES (%s, %s, %s, %s)
           RETURNING id, granted_at""", (tenant_id, user_id, purpose, CONSENT_POLICY_VERSION)).fetchone()
    audit(conn, tenant_id, user_id, "consent.granted", "consent", str(new["id"]), trace_id, purpose.upper())
    emit(conn, tenant_id, "CONSENT_UPDATED", "consent", str(new["id"]), trace_id, {"purpose": purpose, "active": True})
    return {"purpose": purpose, "granted_at": new["granted_at"], "created": True}


def revoke_consent(conn: psycopg.Connection, tenant_id: str, user_id: str, purpose: str, trace_id: str,
                   delete_data: bool) -> dict:
    deleted = 0
    if delete_data and purpose == PLAN_STORAGE:
        # Delete while consent is still live (RLS needs it to see the rows), then revoke.
        deleted = conn.execute("DELETE FROM vb.missions").rowcount
    row = conn.execute("UPDATE vb.consents SET revoked_at = now() WHERE purpose = %s AND revoked_at IS NULL RETURNING id",
                       (purpose,)).fetchone()
    if row is None:
        raise ApiError(404, "NOT_FOUND", "No active consent for that purpose.")
    audit(conn, tenant_id, user_id, "consent.revoked", "consent", str(row["id"]), trace_id,
          "REVOKED_AND_DELETED" if deleted else "REVOKED")
    emit(conn, tenant_id, "CONSENT_UPDATED", "consent", str(row["id"]), trace_id, {"purpose": purpose, "active": False})
    return {"purpose": purpose, "revoked": True, "missions_deleted": deleted}


# ── missions ─────────────────────────────────────────────────────────────────

def create_mission(conn: psycopg.Connection, tenant_id: str, user_id: str, inp: RouterInput, today: date,
                   trace_id: str) -> str:
    if not conn.execute("SELECT vb.has_consent(%s) AS ok", (PLAN_STORAGE,)).fetchone()["ok"]:
        raise ApiError(409, "CONSENT_REQUIRED",
                       "Saving a plan needs your consent first. Nothing was stored. Guest mode works without it.")
    out = kernel.route(inp, today)
    mission_id, case_id = str(uuid.uuid4()), str(uuid.uuid4())
    conn.execute(
        """INSERT INTO vb.missions (id, tenant_id, user_id, policy_version, input_hash, router_input, as_of, stage, track, notices)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (mission_id, tenant_id, user_id, out["policy_version"], out["input_hash"], Jsonb(inp.canonical()), today,
         out["stage"], out["track"], Jsonb(out["notices"])))
    conn.execute("INSERT INTO vb.master_cases (id, tenant_id, user_id, mission_id) VALUES (%s, %s, %s, %s)",
                 (case_id, tenant_id, user_id, mission_id))
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO vb.case_lanes (tenant_id, user_id, case_id, lane, position) VALUES (%s, %s, %s, %s, %s)",
            [(tenant_id, user_id, case_id, lane, i) for i, lane in enumerate(out["lanes"])])
        cur.executemany(
            """INSERT INTO vb.tasks (tenant_id, user_id, case_id, template_id, lane, readiness_dimension, title, why,
                                     confirm_with, priority) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            [(tenant_id, user_id, case_id, t["template_id"], t["lane"], t["dimension"], t["title"], t["why"],
              t["confirm_with"], t["priority"]) for t in out["tasks"]])
    audit(conn, tenant_id, user_id, "mission.created", "mission", mission_id, trace_id)
    emit(conn, tenant_id, "MISSION_CREATED", "mission", mission_id, trace_id, {"case_id": case_id})
    emit(conn, tenant_id, "CASE_CREATED", "master_case", case_id, trace_id,
         {"mission_id": mission_id, "lanes": len(out["lanes"]), "tasks": len(out["tasks"])})
    return mission_id


def list_missions(conn: psycopg.Connection) -> list[dict]:
    return conn.execute(
        """SELECT m.id, m.stage, m.track, m.as_of, m.status, m.created_at, c.id AS case_id
             FROM vb.missions m JOIN vb.master_cases c ON c.mission_id = m.id
            ORDER BY m.created_at DESC LIMIT 50""").fetchall()


def _tasks(conn: psycopg.Connection, case_id) -> list[dict]:
    return conn.execute(
        """SELECT id, template_id, lane, readiness_dimension, title, why, confirm_with, priority, status, version
             FROM vb.tasks WHERE case_id = %s ORDER BY priority, template_id""", (case_id,)).fetchall()


def get_brief(conn: psycopg.Connection, mission_id: str) -> dict:
    m = conn.execute(
        """SELECT m.*, c.id AS case_id, c.status AS case_status
             FROM vb.missions m JOIN vb.master_cases c ON c.mission_id = m.id WHERE m.id = %s""",
        (mission_id,)).fetchone()
    if m is None:
        raise ApiError(404, "NOT_FOUND", "Not found.")
    lanes = [r["lane"] for r in conn.execute(
        "SELECT lane FROM vb.case_lanes WHERE case_id = %s ORDER BY position", (m["case_id"],)).fetchall()]
    tasks = _tasks(conn, m["case_id"])
    open_tasks = [t for t in tasks if t["status"] not in ("done", "cancelled")]
    return {
        "mission_id": m["id"], "case_id": m["case_id"], "privacy_mode": m["privacy_mode"],
        "policy_version": m["policy_version"], "input_hash": m["input_hash"], "as_of": m["as_of"],
        "facts": {"source": "DECLARED", "values": m["router_input"]},
        "stage": m["stage"], "stage_label": vocab.STAGE_LABELS[m["stage"]], "track": m["track"],
        "lanes": lanes, "notices": m["notices"],
        "first_five_actions": open_tasks[:5], "tasks": tasks,
        "readiness": kernel.readiness(tasks),
        "disclosure": language.AI_DISCLOSURE, "disclaimer": language.STANDARD_DISCLAIMER,
    }


def next_action(conn: psycopg.Connection, mission_id: str) -> dict | None:
    brief = get_brief(conn, mission_id)
    return brief["first_five_actions"][0] if brief["first_five_actions"] else None


def get_case(conn: psycopg.Connection, case_id: str) -> dict:
    c = conn.execute("SELECT id, mission_id, status, created_at FROM vb.master_cases WHERE id = %s", (case_id,)).fetchone()
    if c is None:
        raise ApiError(404, "NOT_FOUND", "Not found.")
    lanes = [r["lane"] for r in conn.execute(
        "SELECT lane FROM vb.case_lanes WHERE case_id = %s ORDER BY position", (case_id,)).fetchall()]
    return {**c, "lanes": lanes, "tasks": _tasks(conn, case_id)}


def list_tasks(conn: psycopg.Connection, status: str | None) -> list[dict]:
    if status:
        return conn.execute("""SELECT id, case_id, template_id, title, status, priority, version FROM vb.tasks
                                WHERE status = %s ORDER BY priority, template_id LIMIT 200""", (status,)).fetchall()
    return conn.execute("""SELECT id, case_id, template_id, title, status, priority, version FROM vb.tasks
                            ORDER BY priority, template_id LIMIT 200""").fetchall()


def update_task(conn: psycopg.Connection, tenant_id: str, user_id: str, task_id: str, status: str,
                expected_version: int, trace_id: str) -> dict:
    row = conn.execute(
        """UPDATE vb.tasks SET status = %s, version = version + 1, updated_at = now()
            WHERE id = %s AND version = %s RETURNING id, case_id, status, version""",
        (status, task_id, expected_version)).fetchone()
    if row is None:
        if conn.execute("SELECT 1 FROM vb.tasks WHERE id = %s", (task_id,)).fetchone():
            raise ApiError(409, "VERSION_CONFLICT", "This task changed since you loaded it. Reload and try again.")
        raise ApiError(404, "NOT_FOUND", "Not found.")
    audit(conn, tenant_id, user_id, "task.status_changed", "task", task_id, trace_id, status.upper())
    if status == "done":
        emit(conn, tenant_id, "TASK_COMPLETED", "task", task_id, trace_id, {"case_id": str(row["case_id"])})
    return row


def delete_mission(conn: psycopg.Connection, tenant_id: str, user_id: str, mission_id: str, trace_id: str) -> None:
    if conn.execute("DELETE FROM vb.missions WHERE id = %s", (mission_id,)).rowcount == 0:
        raise ApiError(404, "NOT_FOUND", "Not found.")
    audit(conn, tenant_id, user_id, "mission.deleted", "mission", mission_id, trace_id)
