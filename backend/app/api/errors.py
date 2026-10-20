"""One error contract for every route: code, message, trace_id, retryable.

No stack traces, SQL, or secrets ever reach a response. Not-yours and
does-not-exist both answer 404 so object ids cannot be enumerated.
"""

from __future__ import annotations

import logging
import secrets

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("vetbuddy")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.status, self.code, self.message, self.retryable = status, code, message, retryable


def new_trace_id() -> str:
    return secrets.token_hex(16)


def trace_id(request: Request) -> str:
    tid = getattr(request.state, "trace_id", None)
    if tid is None:
        tid = request.state.trace_id = new_trace_id()
    return tid


def _body(request: Request, status: int, code: str, message: str, retryable: bool = False, **extra) -> JSONResponse:
    return JSONResponse(status_code=status, content={
        "error": {"code": code, "message": message, "trace_id": trace_id(request), "retryable": retryable, **extra}})


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(request: Request, exc: ApiError):
        return _body(request, exc.status, exc.code, exc.message, exc.retryable)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        fields = sorted({".".join(str(p) for p in e["loc"][1:]) or "body" for e in exc.errors()})
        return _body(request, 422, "INVALID_INPUT", "Some fields are missing, unknown or invalid.", fields=fields)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
        return _body(request, exc.status_code, code, "Not found." if exc.status_code == 404 else "Request not allowed.")

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        # Log the type only: exception messages can carry SQL or user input.
        log.error("unhandled %s trace=%s", type(exc).__name__, trace_id(request))
        return _body(request, 500, "INTERNAL", "Something went wrong on our side.", retryable=True)
