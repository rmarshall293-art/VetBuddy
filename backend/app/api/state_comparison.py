"""56-jurisdiction state comparison routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.db.database import get_db
from app.db.models import User
from app.db.schemas import CustomCompareRequest, JurisdictionOut
from app.services import state_comparison_service as scs

router = APIRouter(prefix="/states", tags=["state-comparison"])


@router.get("", response_model=list[JurisdictionOut])
def list_states(db: Session = Depends(get_db)):
    return scs.list_jurisdictions(db)


@router.get("/compare")
def compare_states(
    from_code: str = Query(alias="from"),
    to_code: str = Query(alias="to"),
    db: Session = Depends(get_db),
):
    result = scs.compare(db, from_code, to_code)
    # Serialize ORM objects for JSON response
    return {
        "from_jurisdiction": JurisdictionOut.model_validate(result["from_jurisdiction"]),
        "to_jurisdiction": JurisdictionOut.model_validate(result["to_jurisdiction"]),
        "metrics": result["metrics"],
        "placeholder_warning": result["placeholder_warning"],
        "alabama_quick_compare": result["alabama_quick_compare"],
        "citations": result["citations"],
        "confidence": result["confidence"],
    }


@router.post("/compare/custom")
def custom_compare(
    payload: CustomCompareRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    result = scs.compare(db, payload.from_code, payload.to_code, payload.metrics or None)
    response = {
        "from_jurisdiction": JurisdictionOut.model_validate(result["from_jurisdiction"]),
        "to_jurisdiction": JurisdictionOut.model_validate(result["to_jurisdiction"]),
        "metrics": result["metrics"],
        "placeholder_warning": result["placeholder_warning"],
        "alabama_quick_compare": result["alabama_quick_compare"],
        "citations": result["citations"],
        "confidence": result["confidence"],
    }
    if payload.save:
        if user is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Login required to save comparisons")
        saved = scs.save_comparison(
            db,
            user,
            payload.from_code,
            payload.to_code,
            payload.label,
            payload.metrics,
            {
                "metrics": {k: str(v) for k, v in result["metrics"].items()},
                "confidence": result["confidence"],
            },
        )
        response["saved_id"] = str(saved.id)
    return response


@router.get("/{jurisdiction_id}", response_model=JurisdictionOut)
def get_state(jurisdiction_id: str, db: Session = Depends(get_db)):
    return scs.get_jurisdiction(db, jurisdiction_id)
