"""VetBuddy API (FastAPI modular monolith). Start: uvicorn app.main:app

Guest routes work with no database. Saved plans need APP_DATABASE_URL and a
sign-in mode; without them those routes answer 503 / 401, never a fake success.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api import errors, private, public
from .config import Settings
from .db import Database
from .governance import language


def create_app(settings: Settings | None = None, db: Database | None = None,
               clock: Callable[[], date] = date.today) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="VetBuddy API", version="0.1.0", docs_url="/api/docs", openapi_url="/api/v1/openapi.json",
                  redoc_url=None)
    app.state.settings = settings
    app.state.clock = clock
    app.state.db = db if db is not None else (Database(settings.app_database_url) if settings.app_database_url else None)

    if settings.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False,
                           allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["authorization", "content-type"])

    @app.middleware("http")
    async def envelope_headers(request: Request, call_next):
        tid = errors.trace_id(request)
        response = await call_next(request)
        response.headers["X-Trace-Id"] = tid
        response.headers["X-VetBuddy-Notice"] = "Software, not VA, a VSO, an attorney or a clinician."
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    errors.install(app)
    app.include_router(public.router)
    app.include_router(private.router)

    @app.get("/")
    def root():
        return {"service": "vetbuddy-api", "api": "/api/v1", "notice": language.AI_DISCLOSURE}

    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = create_app()
