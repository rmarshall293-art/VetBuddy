"""
VetBuddy API + web shell (slice 01).

Carried from the skeleton's defect register:
  - ONE prefix, /api/v1.
  - /readyz is the only health endpoint; 503 until the crisis floor verifies
    AND the database answers as the non-owner app role.

Runs on Starlette (FastAPI's foundation) — see docs/ADR/0002. Contracts for
the next routes (benefits, agents, career) are in docs/ARCHITECTURE.md §3.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import sys
import time
import uuid

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from app.api import v1
from app.infra import config
from app.infra.db import DatabaseError, connect
from app.platform.crisis_floor import crisis_floor_satisfied

_log = logging.getLogger("vetbuddy")


def log_event(event: str, **fields) -> None:
    # Structured, PII-free by construction: callers pass ids/codes only.
    _log.info(json.dumps({"event": event, **fields}, default=str))


SECURITY_HEADERS = {
    "content-security-policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' "
                               "https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
                               "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
}


class RequestContext(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.trace_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["x-trace-id"] = request.state.trace_id
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        if request.url.path.startswith("/api/"):
            response.headers["cache-control"] = "no-store"
        log_event("http", trace_id=request.state.trace_id, method=request.method,
                  route=request.scope.get("route").path if request.scope.get("route") else request.url.path,
                  status=response.status_code, ms=round((time.perf_counter() - start) * 1000, 1))
        return response


def create_app(settings: config.Settings | None = None, clock=None) -> Starlette:
    settings = settings or config.load()

    async def readyz(request: Request):
        if not crisis_floor_satisfied():
            return JSONResponse({"status": "not_ready", "reason": "crisis floor not verified"}, status_code=503)
        try:
            with connect(settings.database_url) as conn:
                row = conn.one("SELECT current_user AS u, (SELECT count(*) FROM jurisdiction) AS j")
        except DatabaseError:
            return JSONResponse({"status": "not_ready", "reason": "database unavailable"}, status_code=503)
        return JSONResponse({"status": "ready", "auth_mode": settings.auth_mode,
                             "jurisdictions": row["j"], "mode_c_enabled": settings.mode_c_enabled})

    async def api_not_found(request: Request):
        return v1.error(request, 404, "NOT_FOUND", "Not found.")

    routes = [
        Route("/readyz", readyz, methods=["GET"]),
        *v1.vault_routes(settings, log=log_event),          # /api/v1/vault/... (migration 0014)
        Mount("/api/v1", routes=v1.routes + [Route("/{rest:path}", api_not_found)]),
    ]
    if settings.web_dir.exists():
        routes.append(Mount("/", StaticFiles(directory=str(settings.web_dir), html=True), name="web"))

    app = Starlette(routes=routes, middleware=[Middleware(RequestContext)])
    app.state.settings = settings
    app.state.clock = clock or dt.date.today
    app.state.log = log_event
    return app


if not _log.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(message)s"))
    _log.addHandler(h)
    _log.setLevel(getattr(logging, __import__("os").environ.get("VB_LOG_LEVEL", "INFO").upper(), logging.INFO))

app = create_app()
