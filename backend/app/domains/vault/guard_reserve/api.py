"""Starlette routes under /api/v1/vault/guard-reserve.

Every route is Mode A safe: the Guard & Reserve answers are V1 and are not
stored. A signed-in caller (Mode B) gets the parent agent's grants and pulls,
through the same session rules as the vault (``vault.api``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, List, Optional

from starlette.routing import Route

from .. import api as vault_api
from ..agent import Session
from .agent import GuardReserveAgent

PREFIX = vault_api.PREFIX + "/guard-reserve"


def routes(role: GuardReserveAgent, *, resolver: vault_api.TenantResolver = vault_api.no_sign_in,
           store_factory: Optional[Callable[[str], object]] = None,
           clock: Callable[[], datetime] = vault_api._utc_now) -> List[Route]:

    def guest() -> Session:
        return Session(mode="A", tenant_ref="session-guest")

    def caller(request) -> Session:
        tenant = resolver(request)
        if tenant is None or store_factory is None:
            return guest()
        store = store_factory(tenant)
        return Session(mode="B", tenant_ref=tenant, grants=store, ledger=store, saved=store)

    handle = _handler()

    def catalog(request, body):
        return role.catalog(guest())

    def leads(request, body):
        return role.leads(guest())

    def recovered(request, body):
        return role.recovered_leads(guest(), request.path_params.get("code"))

    def source_queue(request, body):
        return role.source_queue(guest())

    def match(request, body):
        return role.match(body, caller(request), clock())

    return [
        Route(f"{PREFIX}/catalog", handle(catalog), methods=["GET"]),
        Route(f"{PREFIX}/leads", handle(leads), methods=["GET"]),
        Route(f"{PREFIX}/recovered", handle(recovered), methods=["GET"]),
        Route(f"{PREFIX}/recovered/{{code}}", handle(recovered), methods=["GET"]),
        Route(f"{PREFIX}/source-queue", handle(source_queue), methods=["GET"]),
        Route(f"{PREFIX}/match", handle(match), methods=["POST"]),
    ]


def _handler():
    """The vault's own error mapping (one /api/v1 error shape for every route)."""
    from starlette.concurrency import run_in_threadpool
    from starlette.responses import JSONResponse

    from ..agent import ModeError, RequestError
    from ..guards import OutputBlocked

    def handle(fn):
        async def endpoint(request):
            try:
                body = await vault_api._body(request) if request.method == "POST" else {}
                return JSONResponse(await run_in_threadpool(fn, request, body))
            except ModeError as exc:
                return vault_api._error(request, 403, "ACCOUNT_REQUIRED", str(exc))
            except RequestError as exc:
                return vault_api._error(request, 422, "VALIDATION_FAILED", str(exc))
            except OutputBlocked:
                return vault_api._error(request, 500, "OUTPUT_BLOCKED",
                                        "the response was blocked by the governance language guard")
        return endpoint
    return handle
