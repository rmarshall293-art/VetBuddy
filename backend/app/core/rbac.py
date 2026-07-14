"""Role-based access control definitions and helpers."""

from enum import Enum
from typing import Iterable

from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.models import User


class Role(str, Enum):
    VETERAN = "veteran"
    FAMILY_MEMBER = "family_member"
    VSO_RESOURCE_OFFICER = "vso_resource_officer"
    AMERICAN_LEGION_RESOURCE_OFFICER = "american_legion_resource_officer"
    DEPARTMENT_ADMIN = "department_admin"
    SUPER_ADMIN = "super_admin"


ADMIN_ROLES = {Role.DEPARTMENT_ADMIN.value, Role.SUPER_ADMIN.value}
RESOURCE_OFFICER_ROLES = {
    Role.VSO_RESOURCE_OFFICER.value,
    Role.AMERICAN_LEGION_RESOURCE_OFFICER.value,
    *ADMIN_ROLES,
}


def user_role_names(user: User) -> set[str]:
    return {ur.role.name for ur in (user.user_roles or []) if ur.role}


def has_any_role(user: User, roles: Iterable[str]) -> bool:
    return bool(user_role_names(user) & set(roles))


def require_roles(*allowed: str):
    """FastAPI dependency factory enforcing one of the given roles."""

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if not has_any_role(user, allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this resource",
            )
        return user

    return _checker


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not has_any_role(user, ADMIN_ROLES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def require_super_admin(user: User = Depends(get_current_user)) -> User:
    if not has_any_role(user, {Role.SUPER_ADMIN.value}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return user
