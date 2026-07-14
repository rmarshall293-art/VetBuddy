"""Live VA Lighthouse adapter stubs.

TODO (required before production VA integration):
1. Register application at https://developer.va.gov
2. Request access to FHIR R4, Benefits Claims, and Facilities APIs
3. Configure VA_CLIENT_ID, VA_CLIENT_SECRET, VA_REDIRECT_URI
4. Implement PKCE OAuth authorization code flow
5. Keep tokens in short-lived server session / Redis only — never Postgres
6. Minimize PHI/PII retention; prefer session-only responses
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.core.config import get_settings


def create_authorization_session() -> dict[str, Any]:
    settings = get_settings()
    state = uuid4().hex
    # Placeholder URL — replace with full PKCE authorize endpoint when credentials active
    auth_url = (
        f"{settings.va_api_base_url}/oauth2/authorization"
        f"?client_id={settings.va_client_id}"
        f"&redirect_uri={settings.va_redirect_uri}"
        f"&response_type=code&state={state}&scope=openid%20profile%20offline_access"
    )
    return {
        "authorization_url": auth_url,
        "state": state,
        "expires_in": 600,
        "mock": False,
        "note": "Live credential path — complete PKCE and token exchange before production use.",
    }


def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    """
    Exchange authorization code for tokens.

    Returns tokens for in-memory/session use only. Callers MUST NOT persist tokens.
    """
    raise NotImplementedError(
        "Implement token exchange after VA client registration. "
        f"Received code length={len(code)}. Do not store tokens in the database."
    )
