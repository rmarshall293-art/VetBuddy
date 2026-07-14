"""VetBuddy FastAPI application entrypoint."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import (
    admin,
    alabama,
    auth,
    benefits,
    claims,
    evidence,
    forms,
    health,
    payments,
    state_comparison,
    users,
    va_integrations,
)
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.database import Base, engine
from app.db import models  # noqa: F401 — register models

settings = get_settings()
setup_logging(settings.log_level)
logger = get_logger("vetbuddy")


def _init_db() -> None:
    """Create tables for local/dev when migrations have not yet run.

    Production should prefer Alembic / SQL migrations over create_all.
    """
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.warning("Database init deferred: %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    _init_db()
    # Optional Sentry hook — configure SENTRY_DSN in production
    if settings.sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment)
            logger.info("Sentry error tracking initialized")
        except Exception as exc:
            logger.warning("Sentry init skipped: %s", exc)
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "VetBuddy API — veteran benefits, claims analysis, state comparison, "
        "and Alabama resource navigation. Educational guidance only; not legal advice. "
        "VA Lighthouse and Stripe run in mock mode unless live credentials are configured."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_and_security_headers(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.perf_counter()
    # Simple rate-limit placeholder (per-process; use Redis/gateway in production)
    response: Response
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error request_id=%s", request_id)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )
    duration_ms = int((time.perf_counter() - start) * 1000)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Mount routes — both with and without API prefix for health convenience
app.include_router(health.router)
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(claims.router, prefix=settings.api_prefix)
app.include_router(evidence.router, prefix=settings.api_prefix)
app.include_router(forms.router, prefix=settings.api_prefix)
app.include_router(benefits.router, prefix=settings.api_prefix)
app.include_router(state_comparison.router, prefix=settings.api_prefix)
app.include_router(alabama.router, prefix=settings.api_prefix)
app.include_router(va_integrations.router, prefix=settings.api_prefix)
app.include_router(payments.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
        "disclaimer": (
            "Educational guidance and organization support only — not legal advice "
            "or accredited VA representation."
        ),
    }
