"""Authentication routes."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.db.schemas import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services import auth_service
from app.services.audit_service import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    user, tokens = auth_service.register_user(
        db,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        role=payload.role,
        preferred_jurisdiction=payload.preferred_jurisdiction,
    )
    write_audit(
        db,
        action="auth.register",
        actor_user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None,
    )
    return tokens


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    tokens = auth_service.login_user(
        db,
        email=payload.email,
        password=payload.password,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_tokens(db, payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    auth_service.logout(db, payload.refresh_token)
    return MessageResponse(message="Logged out")


@router.delete("/account", response_model=MessageResponse)
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_service.delete_account(db, user)
    write_audit(
        db,
        action="auth.account_deleted",
        actor_user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
    )
    return MessageResponse(message="Account deleted")
