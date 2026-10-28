"""
/api/v1 routes for slice 01.

Each protected handler: resolve principal (one function) -> open ONE
tenant-scoped transaction -> call the domain service -> map domain errors to
the single error contract. Handlers are sync and run in Starlette's
threadpool; each request gets its own connection.
"""
from __future__ import annotations

import datetime as dt
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.domains.missions import router_policy as rp
from app.domains.missions import service as svc
from app.domains.privacy import service as privacy
from app.domains.reference import service as ref
from app.domains.trust import auth, consent
from app.infra.db import DatabaseError, tenant_transaction
from app.platform.crisis_floor import load_crisis_contacts
from app.platform.jurisdiction_status import labelled


# ── error contract ───────────────────────────────────────────────────────────

def error(request: Request, status: int, code: str, message: str, retryable: bool = False, **extra) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "trace_id": request.state.trace_id,
                      "retryable": retryable, **extra}}
    return JSONResponse(body, status_code=status)


def _settings(request: Request):
    return request.app.state.settings


def _today(request: Request) -> dt.date:
    return request.app.state.clock()


def _corr(request: Request) -> str:
    return request.state.trace_id


def protected(handler):
    """Resolve the principal once, run the handler inside a tenant-scoped
    transaction, and translate domain errors. Nothing else checks auth."""
    async def wrapper(request: Request):
        try:
            p = auth.principal_from_header(_settings(request), request.headers.get("authorization"))
        except auth.AuthError:
            return error(request, 401, "UNAUTHENTICATED", "Sign in to continue.")
        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.json() if await request.body() else {}
            except ValueError:
                return error(request, 400, "INVALID_JSON", "Request body must be JSON.")
        from starlette.concurrency import run_in_threadpool

        def run():
            with tenant_transaction(_settings(request).database_url, p.tenant_id) as conn:
                # Fail closed for a deleted or unknown account even when its
                # token is still cryptographically valid (v6 §3, §14 test 2).
                if conn.one("SELECT 1 AS ok FROM app_user WHERE user_id = $1 AND deleted_at IS NULL", [p.user_id]) is None:
                    return error(request, 401, "SESSION_INVALID", "This session is no longer valid. Sign in again.")
                return handler(request, conn, p, body)
        try:
            result = await run_in_threadpool(run)
            if isinstance(result, JSONResponse):
                return result
            return JSONResponse(result)
        except ValidationError as e:
            return error(request, 422, "VALIDATION_FAILED", "Some fields are invalid.",
                         fields=[{"field": ".".join(str(x) for x in err["loc"]), "message": err["msg"]}
                                 for err in e.errors()])
        except rp.RouterInputError as e:
            return error(request, 422, "VALIDATION_FAILED", str(e), fields=[{"field": e.field, "message": str(e)}])
        except privacy.PrivacyError as e:
            return error(request, e.status, e.code, str(e))
        except consent.ConsentRequired as e:
            return error(request, 403, "CONSENT_REQUIRED",
                         "VetBuddy needs your consent to store mission data. You can grant it in Settings.",
                         purpose=e.purpose)
        except svc.NotFound:
            return error(request, 404, "NOT_FOUND", "Not found.")
        except svc.Conflict as e:
            return error(request, 409, e.code, str(e))
        except DatabaseError as e:
            request.app.state.log("db_error", trace_id=request.state.trace_id, sqlstate=e.sqlstate)
            if e.sqlstate in ("40001", "40P01"):
                return error(request, 503, "TRY_AGAIN", "Temporary conflict. Please retry.", retryable=True)
            if e.sqlstate and e.sqlstate.startswith("23"):
                return error(request, 409, "CONSTRAINT_VIOLATION", "That change conflicts with existing data.")
            return error(request, 500, "INTERNAL", "Something went wrong.", retryable=True)
    wrapper.__name__ = handler.__name__
    return wrapper


def _uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise svc.NotFound("id")


# ── request models ───────────────────────────────────────────────────────────

class OnboardingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persona: Literal[rp.PERSONAS]  # type: ignore[valid-type]
    branch: Literal[rp.BRANCHES]  # type: ignore[valid-type]
    component: Literal[rp.COMPONENTS]  # type: ignore[valid-type]
    legal_authority: Optional[Literal[rp.AUTHORITIES]] = None  # type: ignore[valid-type]
    separation_date: Optional[dt.date] = None
    current_jurisdiction: str = Field(min_length=2, max_length=8)
    destination_jurisdiction: Optional[str] = Field(default=None, min_length=2, max_length=8)
    goals: list[Literal[rp.GOALS]] = Field(default_factory=list, max_length=8)  # type: ignore[valid-type]
    urgency: Literal[rp.URGENCIES] = "30_days"  # type: ignore[valid-type]
    display_name: Optional[str] = Field(default=None, max_length=60)
    consent: bool = False

    def router_input(self) -> rp.RouterInput:
        return rp.RouterInput(
            persona=self.persona, branch=self.branch, component=self.component,
            legal_authority=self.legal_authority, separation_date=self.separation_date,
            current_jurisdiction=self.current_jurisdiction.upper(),
            destination_jurisdiction=self.destination_jurisdiction.upper() if self.destination_jurisdiction else None,
            goals=tuple(self.goals), urgency=self.urgency)


class TaskPatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["todo", "in_progress", "blocked", "done", "cancelled"]
    version: int = Field(ge=1)


class PrivacyModeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["A", "B", "C"]


class DeleteAccountIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: str = Field(max_length=40)


class ConsentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose: str = Field(min_length=1, max_length=64)


# ── public routes (Mode A — nothing persisted) ───────────────────────────────

async def crisis_contacts(request: Request):
    return JSONResponse({"contacts": load_crisis_contacts()})


def _public_query(request: Request, fn):
    with tenant_transaction(_settings(request).database_url, None) as conn:
        return fn(conn)


async def list_jurisdictions(request: Request):
    from starlette.concurrency import run_in_threadpool
    rows = await run_in_threadpool(_public_query, request, svc.known_jurisdictions)
    order = {"federal": 0, "state": 1, "territory": 2}
    items = sorted(rows.values(), key=lambda r: (order.get(r["kind"], 3), r["name"]))
    return JSONResponse({"jurisdictions": [labelled(r) for r in items]})


async def preview_brief(request: Request):
    """Guest Mode A. Computes a brief and persists NOTHING (no tenant, no
    rows, no audit). Consent is not needed because nothing is stored."""
    from starlette.concurrency import run_in_threadpool
    try:
        raw = await request.json()
        raw.pop("consent", None)
        raw.pop("display_name", None)
        body = OnboardingIn.model_validate(raw)
    except ValueError as e:
        if isinstance(e, ValidationError):
            return error(request, 422, "VALIDATION_FAILED", "Some fields are invalid.",
                         fields=[{"field": ".".join(str(x) for x in err["loc"]), "message": err["msg"]}
                                 for err in e.errors()])
        return error(request, 400, "INVALID_JSON", "Request body must be JSON.")
    try:
        jur = await run_in_threadpool(_public_query, request, svc.known_jurisdictions)
        return JSONResponse(svc.preview(body.router_input(), jur, _today(request)))
    except rp.RouterInputError as e:
        return error(request, 422, "VALIDATION_FAILED", str(e), fields=[{"field": e.field, "message": str(e)}])


# ── reference corpus (Mode A, V0 public, read-only) ──────────────────────────

async def _ref(request: Request, fn, *args):
    from starlette.concurrency import run_in_threadpool
    try:
        return JSONResponse(await run_in_threadpool(_public_query, request, lambda conn: fn(conn, *args)))
    except ref.UnknownJurisdiction as e:
        return error(request, 404, "UNKNOWN_JURISDICTION", f"No jurisdiction with code {e}.")
    except ref.UnknownCareType as e:
        return error(request, 404, "UNKNOWN_CARE_TYPE", f"No care type {e}.")
    except ref.UnknownRatingCode as e:
        return error(request, 404, "UNKNOWN_RATING_CODE", f"No diagnostic code {e} in the reference schedule.")


async def reference_overview(request: Request):
    return await _ref(request, ref.overview)


async def reference_women_veterans(request: Request):
    q = request.query_params
    return await _ref(request, ref.women_veterans, q.get("jurisdiction"), q.get("care_type"))


async def reference_jurisdiction(request: Request):
    return await _ref(request, ref.jurisdiction_profile, request.path_params["code"])


async def reference_conflicts(request: Request):
    return await _ref(request, ref.conflicts)


async def reference_guard_reserve(request: Request):
    return await _ref(request, ref.guard_reserve)


async def reference_rating_schedule(request: Request):
    return await _ref(request, ref.rating_schedule, request.query_params.get("body_system"))


async def reference_rating_code(request: Request):
    return await _ref(request, ref.rating_code, request.path_params["code"])


async def dev_signup(request: Request):
    """MOCK identity. Exists only when VB_AUTH_MODE=dev."""
    from starlette.concurrency import run_in_threadpool
    s = _settings(request)
    if s.auth_mode != "dev":
        return error(request, 404, "NOT_FOUND", "Not found.")
    tenant_id = uuid.uuid4()

    def run():
        with tenant_transaction(s.database_url, tenant_id) as conn:
            return svc.create_individual_account(conn, tenant_id)
    user_id = await run_in_threadpool(run)
    return JSONResponse({"token": auth.issue_dev_token(s, user_id, tenant_id), "user_id": str(user_id),
                         "auth_method": "dev_mock",
                         "notice": "Development sign-in. Not a real identity provider."}, status_code=201)


# ── protected routes (Mode B) ────────────────────────────────────────────────

@protected
def me(request, conn, p, body):
    return svc.get_me(conn, p)


@protected
def put_privacy_mode(request, conn, p, body):
    m = PrivacyModeIn.model_validate(body)
    return svc.set_privacy_mode(conn, p, m.mode, _settings(request).mode_c_enabled, _corr(request))


@protected
def get_consents(request, conn, p, body):
    return {"consents": svc.list_consents(conn, p)}


@protected
def post_consent(request, conn, p, body):
    return svc.grant_consent(conn, p, ConsentIn.model_validate(body).purpose, _corr(request))


@protected
def post_revoke_consent(request, conn, p, body):
    return svc.revoke_consent(conn, p, _uuid(request.path_params["consent_id"]), _corr(request))


@protected
def post_onboarding(request, conn, p, body):
    m = OnboardingIn.model_validate(body)
    res = svc.onboard(conn, p, m.router_input(), m.display_name, m.consent, _today(request), _corr(request))
    return JSONResponse(res, status_code=201)


@protected
def get_missions(request, conn, p, body):
    return {"missions": svc.list_missions(conn, p)}


@protected
def get_brief(request, conn, p, body):
    return svc.get_brief(conn, p, _uuid(request.path_params["mission_id"]), _today(request))


@protected
def patch_task(request, conn, p, body):
    m = TaskPatchIn.model_validate(body)
    return svc.update_task(conn, p, _uuid(request.path_params["task_id"]), m.status, m.version, _corr(request))


@protected
def get_export(request, conn, p, body):
    data = privacy.export_account(conn, p, _today(request))
    return JSONResponse(data, headers={"content-disposition": 'attachment; filename="vetbuddy-export.json"'})


@protected
def post_delete_account(request, conn, p, body):
    m = DeleteAccountIn.model_validate(body)
    return JSONResponse(privacy.delete_account(conn, p, m.confirm), status_code=200)


async def get_deletion_status(request: Request):
    """Public by unguessable receipt id: the receipt holds no personal data,
    so it can be checked after the account (and its sessions) are gone."""
    from starlette.concurrency import run_in_threadpool
    try:
        rid = uuid.UUID(request.path_params["receipt_id"])
    except ValueError:
        return error(request, 404, "NOT_FOUND", "Not found.")
    try:
        return JSONResponse(await run_in_threadpool(_public_query, request, lambda c: privacy.deletion_status(c, rid)))
    except privacy.PrivacyError as e:
        return error(request, e.status, e.code, str(e))


routes = [
    Route("/crisis-contacts", crisis_contacts, methods=["GET"]),
    Route("/jurisdictions", list_jurisdictions, methods=["GET"]),
    Route("/brief/preview", preview_brief, methods=["POST"]),
    Route("/reference", reference_overview, methods=["GET"]),
    Route("/reference/women-veterans", reference_women_veterans, methods=["GET"]),
    Route("/reference/jurisdictions/{code}", reference_jurisdiction, methods=["GET"]),
    Route("/reference/conflicts", reference_conflicts, methods=["GET"]),
    Route("/reference/guard-reserve", reference_guard_reserve, methods=["GET"]),
    Route("/reference/rating-schedule", reference_rating_schedule, methods=["GET"]),
    Route("/reference/rating-schedule/{code}", reference_rating_code, methods=["GET"]),
    Route("/dev/signup", dev_signup, methods=["POST"]),
    Route("/me", me, methods=["GET"]),
    Route("/me/privacy-mode", put_privacy_mode, methods=["PUT"]),
    Route("/me/export", get_export, methods=["GET"]),
    Route("/me/delete", post_delete_account, methods=["POST"]),
    Route("/privacy/deletions/{receipt_id}", get_deletion_status, methods=["GET"]),
    Route("/consents", get_consents, methods=["GET"]),
    Route("/consents", post_consent, methods=["POST"]),
    Route("/consents/{consent_id}/revoke", post_revoke_consent, methods=["POST"]),
    Route("/onboarding", post_onboarding, methods=["POST"]),
    Route("/missions", get_missions, methods=["GET"]),
    Route("/missions/{mission_id}/brief", get_brief, methods=["GET"]),
    Route("/tasks/{task_id}", patch_task, methods=["PATCH"]),
]


# ── Benefit Vault (migration 0014; routes under /api/v1/vault) ───────────────
#
# The vault ships its own Starlette routes (app/domains/vault/api.py). They are
# mounted by create_app with the platform's session rules: a Mode B (account)
# request needs the same thing every protected route needs (a valid token, an
# app_user row that still exists, and active consent to store data), checked in
# one tenant-scoped transaction. Anything less is a guest (Mode A) request, so
# guest search and matching never need an account (v6 §2) and a deleted
# account's token fails closed (v6 §3). The pull grant itself is the
# purpose-bound consent for pulls (benefit_matching), confirmed through the
# vault's ApprovalGate.

def vault_tenant(request: Request) -> Optional[str]:
    settings = _settings(request)
    try:
        p = auth.principal_from_header(settings, request.headers.get("authorization"))
    except auth.AuthError:
        return None
    try:
        with tenant_transaction(settings.database_url, p.tenant_id) as conn:
            if conn.one("SELECT 1 AS ok FROM app_user WHERE user_id = $1 AND deleted_at IS NULL", [p.user_id]) is None:
                return None
            if consent.active_consent(conn, p.user_id, consent.MISSION_PURPOSE) is None:
                return None
    except DatabaseError:
        return None
    return str(p.tenant_id)


def vault_routes(settings, log=None) -> list:
    """Build the vault agent once (registry plus any named-reviewer VERIFIED marks
    kept in the database, gate G1) and return its routes."""
    from app.domains.vault import api as vault_api
    from app.domains.vault.agent import BenefitVaultAgent
    from app.domains.vault.registry import default_registry
    from app.domains.vault.vault_store import VaultStore, load_reviews
    from app.infra import pg_compat

    registry = default_registry()
    try:
        with pg_compat.connect(settings.database_url) as conn:
            registry = registry.with_reviews(load_reviews(conn))
    except pg_compat.Error as exc:
        # Without the database no review can be applied: every record keeps its
        # registry status (none is VERIFIED), which only ever shows less.
        if log:
            log("vault_reviews_unavailable", sqlstate=exc.sqlstate)
    agent = BenefitVaultAgent(registry)

    def store_factory(tenant: str):
        return VaultStore(connect=lambda: pg_compat.connect(settings.database_url))

    return vault_api.routes(agent, resolver=vault_tenant, store_factory=store_factory)
