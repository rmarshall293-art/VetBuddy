"""Benefits search routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Benefit
from app.db.schemas import BenefitOut

router = APIRouter(prefix="/benefits", tags=["benefits"])


@router.get("", response_model=list[BenefitOut])
def list_benefits(
    jurisdiction: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Benefit)
    if jurisdiction:
        q = q.filter(Benefit.jurisdiction_code == jurisdiction.upper())
    if category:
        q = q.filter(Benefit.category.ilike(f"%{category}%"))
    return q.order_by(Benefit.name).limit(200).all()


@router.get("/search", response_model=list[BenefitOut])
def search_benefits(q: str = Query(min_length=1), db: Session = Depends(get_db)):
    pattern = f"%{q}%"
    return (
        db.query(Benefit)
        .filter(
            (Benefit.name.ilike(pattern))
            | (Benefit.summary.ilike(pattern))
            | (Benefit.category.ilike(pattern))
        )
        .order_by(Benefit.name)
        .limit(100)
        .all()
    )
