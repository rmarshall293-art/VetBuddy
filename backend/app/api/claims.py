"""Claims CRUD routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.db.schemas import ClaimCreate, ClaimOut, ClaimUpdate, MessageResponse
from app.services import claims_service
from app.services.audit_service import write_audit

router = APIRouter(prefix="/claims", tags=["claims"])


@router.get("", response_model=list[ClaimOut])
def list_claims(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return claims_service.list_claims(db, user)


@router.post("", response_model=ClaimOut, status_code=201)
def create_claim(
    payload: ClaimCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = claims_service.create_claim(db, user, payload)
    write_audit(
        db,
        action="claims.create",
        actor_user_id=user.id,
        resource_type="claim",
        resource_id=str(claim.id),
    )
    return claim


@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim(
    claim_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return claims_service.get_claim(db, user, claim_id)


@router.patch("/{claim_id}", response_model=ClaimOut)
def update_claim(
    claim_id: UUID,
    payload: ClaimUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return claims_service.update_claim(db, user, claim_id, payload)


@router.delete("/{claim_id}", response_model=MessageResponse)
def delete_claim(
    claim_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claims_service.delete_claim(db, user, claim_id)
    return MessageResponse(message="Claim deleted")
