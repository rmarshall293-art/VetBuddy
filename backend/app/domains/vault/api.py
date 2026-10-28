"""Starlette routes under /api/v1/vault.

Mode A routes (catalog, search, read, match, household, governance, leads,
discovery plan) are stateless and safe for a guest: they hold nothing and
accept only V1 facts. Mode B routes (grants, ledger, saved benefits) need an
authenticated tenant. Slice 03 has no sign-in for the vault yet (gate G17),
so the default tenant resolver returns None and those routes answer 403; the
tests inject a resolver and a database-backed store.

Integration: add ``vault_routes.routes(agent)`` to ``backend/app/api/v1.py``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable, List, Optional

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .agent import BenefitVaultAgent, ModeError, RequestError, Session
from .discovery.planner import DiscoveryPlanner
from .guards import ApprovalRequired, OutputBlocked
from .vault_store import StoreError

PREFIX = "/api/v1/vault"
MAX_BODY = 64 * 1024

TenantResolver = Callable[[Request], Optional[str]]


def no_sign_in(request: Request) -> Optional[str]:
    """The production default until G17 wires authentication: everyone is a guest."""
    return None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _error(request: Request, status: int, code: str, message: str, retryable: bool = False, **extra) -> JSONResponse:
    """The /api/v1 error contract (app/api/v1.py ``error``): one shape for every route."""
    trace_id = getattr(request.state, "trace_id", None)
    return JSONResponse({"error": {"code": code, "message": message, "trace_id": trace_id,
                                   "retryable": retryable, **extra}}, status_code=status)


async def _body(request: Request) -> dict:
    raw = await request.body()
    if len(raw) > MAX_BODY:
        raise RequestError("request body is too large")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        raise RequestError("request body is not JSON") from None
    if not isinstance(data, dict):
        raise RequestError("request body is a JSON object")
    return data


def _list_param(request: Request, name: str) -> Optional[List[str]]:
    values = []
    for raw in request.query_params.getlist(name):
        values.extend(v for v in raw.split(",") if v)
    return values or None


def routes(agent: BenefitVaultAgent, *, resolver: TenantResolver = no_sign_in,
           store_factory: Optional[Callable[[str], object]] = None,
           clock: Callable[[], datetime] = _utc_now) -> List[Route]:
    planner = DiscoveryPlanner(agent.registry, agent.egress)

    def guest() -> Session:
        return Session(mode="A", tenant_ref="session-guest")

    def account(request: Request) -> Session:
        tenant = resolver(request)
        if tenant is None or store_factory is None:
            raise ModeError("this needs a signed-in private account with consent to store data; "
                            "production sign-in waits on G17")
        store = store_factory(tenant)
        return Session(mode="B", tenant_ref=tenant, grants=store, ledger=store, saved=store)

    def caller(request: Request) -> Session:
        tenant = resolver(request)
        return account(request) if tenant is not None and store_factory is not None else guest()

    def handle(fn):
        async def endpoint(request: Request):
            try:
                return JSONResponse(await fn(request))
            except ApprovalRequired as exc:
                return _error(request, 409, "APPROVAL_REQUIRED", "confirmation needed",
                              approval_required=exc.action, consent_text=exc.consent_text)
            except ModeError as exc:
                return _error(request, 403, "ACCOUNT_REQUIRED", str(exc))
            except RequestError as exc:
                return _error(request, 422, "VALIDATION_FAILED", str(exc))
            except KeyError as exc:
                return _error(request, 404, "NOT_FOUND", f"not found: {exc.args[0] if exc.args else ''}")
            except StoreError as exc:
                return _error(request, 400, "BAD_REQUEST", str(exc))
            except OutputBlocked:
                return _error(request, 500, "OUTPUT_BLOCKED", "the response was blocked by the governance language guard")
        return endpoint

    async def catalog(request):
        registry = agent.registry
        return {
            **registry.describe(),
            "notice": registry.notice,
            "governing_sentence": registry.data["governing_sentence"],
            "outcomes": registry.data["vocabulary"]["outcomes"],
            "categories": registry.data["vocabulary"]["categories"],
            "groups": registry.data["vocabulary"]["groups"],
            "tiers": registry.data["vocabulary"]["tiers"],
            "rule_tokens": registry.data["vocabulary"]["tokens"],
            "parametric_tokens": registry.data["vocabulary"]["parametric_tokens"],
            "facts": {k: {"data_class": v["data_class"], "question": v["question"], "values": v["values"]}
                      for k, v in registry.data["facts"].items()},
            "jurisdictions": [{k: j[k] for k in ("code", "name", "coverage", "benefit_count", "tail_unread_chars")}
                              for j in registry.data["jurisdictions"]],
            "publish_policy": registry.publish_policy(agent.environment),
        }

    async def search(request):
        params = request.query_params
        query = {"q": params.get("q", ""), "jurisdictions": _list_param(request, "jurisdiction"),
                 "categories": _list_param(request, "category"), "groups": _list_param(request, "group"),
                 "kinds": _list_param(request, "kind"), "limit": params.get("limit", "25"),
                 "offset": params.get("offset", "0")}
        return agent.search(query, guest())

    async def read(request):
        return agent.benefit(request.path_params["benefit_id"], guest())

    async def match(request):
        body = await _body(request)
        return agent.match(body, caller(request), clock())

    async def household(request):
        body = await _body(request)
        return agent.household(body, caller(request), clock())

    async def governance(request):
        registry = agent.registry
        policy = registry.governance
        return {
            "governing_sentence": registry.data["governing_sentence"],
            "agents": agent.manifests.public_view(),
            "mode_ceiling": policy["mode_ceiling"],
            "never_pullable": policy["never_pullable"],
            "pull_purposes": policy["pull_purposes"],
            "grants": policy["grants"],
            "packets": policy["packets"],
            "publish_policy": registry.publish_policy(agent.environment),
            "components": registry.data["components"],
        }

    async def leads(request):
        registry = agent.registry
        return {"rule_leads": list(registry.rule_leads.values()), "recovered_leads": registry.recovered_leads,
                "license_reciprocity": registry.data["license_reciprocity"],
                "caveat": registry.caveats["recovered_lead"]}

    async def discovery(request):
        try:
            limit = int(request.query_params.get("limit", "50"))
            tasks = planner.plan(limit=limit)
        except ValueError as exc:
            raise RequestError(str(exc)) from None
        return {"executable": planner.executable, "tasks": [t.view() for t in tasks]}

    async def grants_list(request):
        return agent.grants(account(request), clock())

    async def grants_create(request):
        body = await _body(request)
        return agent.create_grant(body, account(request), clock())

    async def grants_revoke(request):
        return agent.revoke_grant(request.path_params["grant_id"], account(request), clock())

    async def ledger(request):
        return agent.ledger(account(request))

    async def saved_list(request):
        return agent.saved(account(request))

    async def saved_create(request):
        body = await _body(request)
        return agent.save_benefit(body, account(request))

    async def saved_discard(request):
        body = await _body(request)
        session = account(request)
        agent.approval.require("discard_saved", body.get("confirm"), "Remove this benefit from your list.")
        return {"removed": session.saved.discard(session.tenant_ref, "saved_benefit", request.path_params["saved_id"])}

    return [
        Route(f"{PREFIX}/catalog", handle(catalog), methods=["GET"]),
        Route(f"{PREFIX}/benefits", handle(search), methods=["GET"]),
        Route(f"{PREFIX}/benefits/{{benefit_id}}", handle(read), methods=["GET"]),
        Route(f"{PREFIX}/match", handle(match), methods=["POST"]),
        Route(f"{PREFIX}/household", handle(household), methods=["POST"]),
        Route(f"{PREFIX}/governance", handle(governance), methods=["GET"]),
        Route(f"{PREFIX}/leads", handle(leads), methods=["GET"]),
        Route(f"{PREFIX}/discovery/plan", handle(discovery), methods=["GET"]),
        Route(f"{PREFIX}/grants", handle(grants_list), methods=["GET"]),
        Route(f"{PREFIX}/grants", handle(grants_create), methods=["POST"]),
        Route(f"{PREFIX}/grants/{{grant_id}}/revoke", handle(grants_revoke), methods=["POST"]),
        Route(f"{PREFIX}/ledger", handle(ledger), methods=["GET"]),
        Route(f"{PREFIX}/saved", handle(saved_list), methods=["GET"]),
        Route(f"{PREFIX}/saved", handle(saved_create), methods=["POST"]),
        Route(f"{PREFIX}/saved/{{saved_id}}/discard", handle(saved_discard), methods=["POST"]),
    ]
