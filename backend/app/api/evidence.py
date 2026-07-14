"""Evidence routes for claims."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.db.schemas import EvidenceCreate, EvidenceOut
from app.services import claims_service

router = APIRouter(tags=["evidence"])


@router.get("/claims/{claim_id}/evidence", response_model=list[EvidenceOut])
def list_evidence(
    claim_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return claims_service.list_evidence(db, user, claim_id)


@router.post("/claims/{claim_id}/evidence", response_model=EvidenceOut, status_code=201)
def create_evidence(
    claim_id: UUID,
    payload: EvidenceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return claims_service.add_evidence(db, user, claim_id, payload)
