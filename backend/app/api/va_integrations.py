"""VA mock and Lighthouse session routes."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.db.database import get_db
from app.db.models import User
from app.services import va_lighthouse_service

router = APIRouter(prefix="/va", tags=["va"])


@router.get("/mock/profile")
def mock_profile():
    return va_lighthouse_service.get_mock_profile()


@router.get("/mock/claims")
def mock_claims():
    return {"claims": va_lighthouse_service.get_mock_claims(), "data_status": "mock"}


@router.post("/lighthouse/session")
def lighthouse_session(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    return va_lighthouse_service.start_lighthouse_session(
        db,
        user_id=user.id if user else None,
        request_id=request.headers.get("x-request-id"),
    )
