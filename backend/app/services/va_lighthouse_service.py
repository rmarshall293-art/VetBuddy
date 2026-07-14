"""VA Lighthouse integration façade — mock by default; live adapter when credentials exist."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations import va_lighthouse, va_mock
from app.services.audit_service import log_api_integration


def get_mock_profile() -> dict[str, Any]:
    return va_mock.mock_veteran_profile()


def get_mock_claims() -> list[dict[str, Any]]:
    return va_mock.mock_claims()


def start_lighthouse_session(
    db: Session,
    *,
    user_id: Optional[UUID] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Begin a VA OAuth session.

    IMPORTANT:
    - Tokens are session-only and must NOT be persisted to the database.
    - Without live credentials, returns a mock authorization URL/session.
    - Register an app at https://developer.va.gov for production/sandbox keys.
    """
    settings = get_settings()
    if settings.va_mock_mode or not settings.va_client_id:
        result = va_mock.mock_lighthouse_session()
        provider = "va_mock"
    else:
        result = va_lighthouse.create_authorization_session()
        provider = "va_lighthouse"

    log_api_integration(
        db,
        provider=provider,
        endpoint="/oauth2/authorization",
        http_status=200,
        success=True,
        user_id=user_id,
        request_id=request_id,
        meta={"mock": settings.va_mock_mode or not settings.va_client_id},
    )
    # Explicitly ensure no token fields are written to durable storage
    safe = {k: v for k, v in result.items() if k not in {"access_token", "refresh_token", "id_token"}}
    return safe
