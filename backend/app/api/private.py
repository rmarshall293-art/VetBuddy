"""Signed-in routes (Privacy Mode B). Every handler gets a Principal from the
verified token and runs in one scoped transaction; RLS decides visibility.

Cross-user and cross-tenant ids answer 404, the same as ids that don't exist.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from ..auth import AuthError, Principal, mint_dev_token, verify_token
from ..kernel import router as kernel
from ..services import work
from .errors import ApiError, trace_id
from .public import today
from .schemas import ConsentRequest, DevTokenRequest, RouterRequest, TaskUpdate

router = APIRouter(prefix="/api/v1")


def require_db(request: Request):
    db = request.app.state.db
    if db is None:
        raise ApiError(503, "STORAGE_UNAVAILABLE", "Saved plans are not available on this server. Guest mode still works.",
                       retryable=True)
    return db


def principal(request: Request) -> Principal:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise ApiError(401, "UNAUTHENTICATED", "Sign in to use saved plans.")
    try:
        tenant_slug, subject = verify_token(request.app.state.settings, header[7:].strip())
    except AuthError:
        raise ApiError(401, "UNAUTHENTICATED", "Sign in to use saved plans.") from None
    db = require_db(request)
    with db.unscoped() as conn:
        row = conn.execute("SELECT tenant_id, user_id FROM vb.resolve_principal(%s, %s)", (tenant_slug, subject)).fetchone()
    if row is None:
        raise ApiError(401, "UNAUTHENTICATED", "Sign in to use saved plans.")
    return Principal(tenant_id=str(row["tenant_id"]), user_id=str(row["user_id"]), subject=subject,
                     tenant_slug=tenant_slug)


@router.post("/dev/token", include_in_schema=False)
def dev_token(body: DevTokenRequest, request: Request):
    """Development-only sign-in stand-in. Refused unless AUTH_MODE=dev."""
    try:
        return {"access_token": mint_dev_token(request.app.state.settings, body.subject, body.tenant),
                "token_type": "bearer", "mock": True}
    except AuthError:
        raise ApiError(404, "NOT_FOUND", "Not found.") from None


@router.get("/users/me")
def me(request: Request, p: Principal = Depends(principal)):
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        consents = work.active_consents(conn)
    return {"user_id": p.user_id, "tenant": p.tenant_slug, "privacy_mode": "B", "consents": consents,
            "sign_in": "dev_mock"}


@router.post("/consents", status_code=201)
def grant(body: ConsentRequest, request: Request, p: Principal = Depends(principal)):
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        return work.grant_consent(conn, p.tenant_id, p.user_id, body.purpose, trace_id(request))


@router.delete("/consents/{purpose}")
def revoke(purpose: str, request: Request, delete_data: bool = False, p: Principal = Depends(principal)):
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        return work.revoke_consent(conn, p.tenant_id, p.user_id, purpose, trace_id(request), delete_data)


@router.post("/missions", status_code=201)
def create_mission(body: RouterRequest, request: Request, p: Principal = Depends(principal)):
    try:
        inp = body.to_input()
        kernel.validate(inp)
    except kernel.RouterInputError as e:
        raise ApiError(422, "INVALID_INPUT", str(e)) from None
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        mission_id = work.create_mission(conn, p.tenant_id, p.user_id, inp, today(request), trace_id(request))
        return work.get_brief(conn, mission_id)


@router.get("/missions")
def missions(request: Request, p: Principal = Depends(principal)):
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        return {"missions": work.list_missions(conn)}


@router.get("/missions/{mission_id}")
def mission(mission_id: UUID, request: Request, p: Principal = Depends(principal)):
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        return work.get_brief(conn, str(mission_id))


@router.get("/missions/{mission_id}/next-action")
def mission_next_action(mission_id: UUID, request: Request, p: Principal = Depends(principal)):
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        return {"next_action": work.next_action(conn, str(mission_id))}


@router.delete("/missions/{mission_id}", status_code=204)
def delete_mission(mission_id: UUID, request: Request, p: Principal = Depends(principal)):
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        work.delete_mission(conn, p.tenant_id, p.user_id, str(mission_id), trace_id(request))


@router.get("/cases/{case_id}")
def case(case_id: UUID, request: Request, p: Principal = Depends(principal)):
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        return work.get_case(conn, str(case_id))


@router.get("/tasks")
def tasks(request: Request, status: Literal["todo", "in_progress", "done", "cancelled"] | None = None,
          p: Principal = Depends(principal)):
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        return {"tasks": work.list_tasks(conn, status)}


@router.patch("/tasks/{task_id}")
def update_task(task_id: UUID, body: TaskUpdate, request: Request, p: Principal = Depends(principal)):
    with request.app.state.db.scoped(p.tenant_id, p.user_id) as conn:
        return work.update_task(conn, p.tenant_id, p.user_id, str(task_id), body.status, body.expected_version,
                                trace_id(request))
