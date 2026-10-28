"""
current_principal() — the ONE auth swap point (skeleton README / main.py note).

Status: MOCK. In VB_AUTH_MODE=dev, tokens are HMAC-signed
"vbdev.<user_id>.<tenant_id>.<expiry>.<sig>" strings issued by the dev
signup route. Real identity (OIDC / ID.me / Microsoft, 10-minute access +
rotating refresh per Master Record default #3) replaces `verify_token`
only — no route body checks auth itself.

Any other mode rejects every protected request (fail closed).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import time
import uuid
from dataclasses import dataclass

from app.infra.config import Settings

DEV_TOKEN_TTL_SECONDS = 8 * 3600


@dataclass(frozen=True)
class Principal:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    auth_method: str            # "dev_mock"


class AuthError(Exception):
    pass


def _sig(secret: bytes, body: str) -> str:
    mac = hmac.new(secret, body.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac).decode().rstrip("=")


def issue_dev_token(settings: Settings, user_id: uuid.UUID, tenant_id: uuid.UUID, now: float | None = None) -> str:
    if settings.auth_mode != "dev":
        raise AuthError("dev tokens are disabled")
    exp = int((now or time.time()) + DEV_TOKEN_TTL_SECONDS)
    body = f"vbdev.{user_id}.{tenant_id}.{exp}"
    return f"{body}.{_sig(settings.dev_token_secret, body)}"


def verify_token(settings: Settings, token: str, now: float | None = None) -> Principal:
    if settings.auth_mode != "dev":
        raise AuthError("authentication is not configured")
    parts = token.split(".")
    if len(parts) != 5 or parts[0] != "vbdev":
        raise AuthError("malformed token")
    body = ".".join(parts[:4])
    if not hmac.compare_digest(_sig(settings.dev_token_secret, body), parts[4]):
        raise AuthError("bad signature")
    if int(parts[3]) < (now or time.time()):
        raise AuthError("token expired")
    try:
        return Principal(uuid.UUID(parts[1]), uuid.UUID(parts[2]), "dev_mock")
    except ValueError as e:
        raise AuthError("malformed token") from e


def principal_from_header(settings: Settings, authorization: str | None) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("missing bearer token")
    return verify_token(settings, authorization[len("Bearer "):].strip())
