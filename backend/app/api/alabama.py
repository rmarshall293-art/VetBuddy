"""Alabama-specific resource routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services import alabama_service

router = APIRouter(prefix="/alabama", tags=["alabama"])


@router.get("/benefits")
def alabama_benefits():
    return {
        "jurisdiction": "AL",
        "placeholder_warning": True,
        "benefits": alabama_service.get_alabama_benefits(),
        "disclaimer": (
            "Educational resource navigation only. Verify eligibility with ADVA, "
            "county VSOs, or accredited representatives."
        ),
    }


@router.get("/resource-officer-training")
def resource_officer_training():
    return alabama_service.resource_officer_training()


@router.get("/county-offices")
def county_offices(db: Session = Depends(get_db)):
    return {
        "jurisdiction": "AL",
        "offices": alabama_service.get_county_offices(db),
        "data_status": "placeholder",
    }


@router.get("/ranking")
def ranking(db: Session = Depends(get_db)):
    return alabama_service.alabama_ranking(db)
