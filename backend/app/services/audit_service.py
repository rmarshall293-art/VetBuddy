"""Audit logging helpers — metadata only, no sensitive VA payloads."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import ApiIntegrationLog, AuditLog


def write_audit(
    db: Session,
    *,
    action: str,
    actor_user_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    commit: bool = True,
) -> AuditLog:
    row = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        request_id=request_id,
        details=details or {},
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    return row


def log_api_integration(
    db: Session,
    *,
    provider: str,
    endpoint: str,
    http_status: Optional[int] = None,
    duration_ms: Optional[int] = None,
    request_id: Optional[str] = None,
    user_id: Optional[UUID] = None,
    success: bool = True,
    meta: Optional[dict[str, Any]] = None,
) -> ApiIntegrationLog:
    row = ApiIntegrationLog(
        provider=provider,
        endpoint=endpoint,
        http_status=http_status,
        duration_ms=duration_ms,
        request_id=request_id,
        user_id=user_id,
        success=success,
        meta=meta or {},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
