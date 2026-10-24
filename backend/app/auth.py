"""Sign-in: development tokens behind one swap point (status: MOCK, gap G17).

A real identity provider (decision G17: ID.me + Microsoft, short-lived access
tokens) replaces `verify_token` only. Everything downstream consumes a
`Principal`, whose subject is bound from the verified token — never from the
request body (R12: acts only for the signed-in person).

Dev token = base64url(json payload) + "." + base64url(HMAC-SHA256(payload)).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from .config import Settings

MAX_TTL_SECONDS = 600  # 10-minute access tokens, per the recommended G17 default


class AuthError(Exception):
    pass


@dataclass(frozen=True)
class Principal:
    tenant_id: str
    user_id: str
    subject: str
    tenant_slug: str


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def mint_dev_token(settings: Settings, subject: str, tenant: str = "public", ttl: int = MAX_TTL_SECONDS,
                   now: float | None = None) -> str:
    if settings.auth_mode != "dev":
        raise AuthError("development tokens are disabled")
    now = time.time() if now is None else now
    payload = _b64(json.dumps({"sub": subject, "ten": tenant, "exp": int(now) + min(ttl, MAX_TTL_SECONDS)},
                              sort_keys=True, separators=(",", ":")).encode())
    sig = hmac.new(settings.auth_dev_secret.encode(), payload.encode(), hashlib.sha256).digest()
    return f"{payload}.{_b64(sig)}"


def verify_token(settings: Settings, token: str, now: float | None = None) -> tuple[str, str]:
    """Return (tenant_slug, subject) or raise AuthError. The swap point for a real IdP."""
    if settings.auth_mode != "dev":
        raise AuthError("sign-in is not available")
    try:
        payload, sig = token.split(".")
        want = hmac.new(settings.auth_dev_secret.encode(), payload.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(want, _unb64(sig)):
            raise AuthError("bad signature")
        claims = json.loads(_unb64(payload))
    except AuthError:
        raise
    except Exception as e:  # malformed token of any kind
        raise AuthError("malformed token") from e
    if not isinstance(claims, dict) or not isinstance(claims.get("sub"), str) or not isinstance(claims.get("ten"), str):
        raise AuthError("malformed token")
    if not isinstance(claims.get("exp"), int) or claims["exp"] < (time.time() if now is None else now):
        raise AuthError("token expired")
    return claims["ten"], claims["sub"]
