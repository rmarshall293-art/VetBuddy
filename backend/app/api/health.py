"""Health check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.db.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"
    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        database=db_status,
        va_mode="mock" if settings.va_mock_mode or not settings.va_client_id else "live",
        stripe_mode="mock" if settings.stripe_mock_mode or not settings.stripe_secret_key else "live",
    )
