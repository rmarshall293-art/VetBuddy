"""Auth service — registration, login, refresh rotation, account deletion."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.rbac import Role
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    safe_decode_token,
    verify_password,
)
from app.db.models import Role as RoleModel
from app.db.models import Session as DbSession
from app.db.models import Subscription, User, UserProfile, UserRole
from app.db.schemas import TokenResponse, UserOut


ALLOWED_SELF_REGISTER_ROLES = {
    Role.VETERAN.value,
    Role.FAMILY_MEMBER.value,
}


def _role_names(user: User) -> list[str]:
    return [ur.role.name for ur in (user.user_roles or []) if ur.role]


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        mfa_enabled=user.mfa_enabled,
        roles=_role_names(user),
        profile=user.profile,
        created_at=user.created_at,
    )


def _ensure_role(db: Session, name: str) -> RoleModel:
    role = db.query(RoleModel).filter(RoleModel.name == name).first()
    if role is None:
        role = RoleModel(name=name, description=f"Auto-created role: {name}")
        db.add(role)
        db.flush()
    return role


def register_user(
    db: Session,
    *,
    email: str,
    password: str,
    display_name: Optional[str] = None,
    role: str = Role.VETERAN.value,
    preferred_jurisdiction: Optional[str] = "AL",
) -> tuple[User, TokenResponse]:
    if role not in ALLOWED_SELF_REGISTER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-registration limited to veteran or family_member roles",
        )
    existing = db.query(User).filter(User.email == email.lower(), User.deleted_at.is_(None)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.flush()

    db.add(
        UserProfile(
            user_id=user.id,
            display_name=display_name or email.split("@")[0],
            preferred_jurisdiction=preferred_jurisdiction,
        )
    )
    role_row = _ensure_role(db, role)
    db.add(UserRole(user_id=user.id, role_id=role_row.id))
    db.add(Subscription(user_id=user.id, tier="free", status="active"))
    db.flush()

    tokens = _issue_tokens(db, user)
    db.commit()
    db.refresh(user)
    return user, tokens


def login_user(
    db: Session,
    *,
    email: str,
    password: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> TokenResponse:
    user = (
        db.query(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .filter(User.email == email.lower(), User.deleted_at.is_(None))
        .first()
    )
    if user is None or not user.hashed_password or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    user.last_login_at = datetime.now(timezone.utc)
    tokens = _issue_tokens(db, user, user_agent=user_agent, ip_address=ip_address)
    db.commit()
    return tokens


def refresh_tokens(db: Session, refresh_token: str) -> TokenResponse:
    payload = safe_decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    jti = payload.get("jti")
    session = (
        db.query(DbSession)
        .filter(DbSession.refresh_token_jti == jti, DbSession.revoked_at.is_(None))
        .first()
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session expired")
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session expired")

    # Rotate: revoke old, issue new
    session.revoked_at = datetime.now(timezone.utc)
    user = (
        db.query(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .filter(User.id == session.user_id, User.deleted_at.is_(None))
        .first()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    tokens = _issue_tokens(db, user)
    db.commit()
    return tokens


def logout(db: Session, refresh_token: Optional[str] = None) -> None:
    if not refresh_token:
        return
    payload = safe_decode_token(refresh_token)
    if not payload:
        return
    jti = payload.get("jti")
    session = db.query(DbSession).filter(DbSession.refresh_token_jti == jti).first()
    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()


def delete_account(db: Session, user: User) -> None:
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    user.email = f"deleted+{user.id}@vetbuddy.local"
    for session in db.query(DbSession).filter(DbSession.user_id == user.id, DbSession.revoked_at.is_(None)):
        session.revoked_at = datetime.now(timezone.utc)
    db.commit()


def _issue_tokens(
    db: Session,
    user: User,
    *,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> TokenResponse:
    settings = get_settings()
    roles = _role_names(user)
    access = create_access_token(str(user.id), roles=roles)
    refresh, jti, expires = create_refresh_token(str(user.id))
    db.add(
        DbSession(
            user_id=user.id,
            refresh_token_jti=jti,
            expires_at=expires,
            user_agent=user_agent,
            ip_address=ip_address,
        )
    )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )
