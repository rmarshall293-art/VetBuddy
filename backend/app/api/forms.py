"""VA forms and intent-to-file guidance."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import VaForm
from app.db.schemas import VaFormOut
from app.services.claims_service import intent_to_file_checklist

router = APIRouter(tags=["forms"])


DEFAULT_FORMS = [
    {
        "form_number": "21-526EZ",
        "title": "Application for Disability Compensation",
        "category": "disability",
        "url": "https://www.va.gov/find-forms/about-form-21-526ez/",
        "guidance": "Primary disability compensation application. Educational guidance only.",
    },
    {
        "form_number": "21-0966",
        "title": "Intent to File a Claim",
        "category": "intent_to_file",
        "url": "https://www.va.gov/find-forms/about-form-21-0966/",
        "guidance": "Preserves potential effective date while gathering evidence.",
    },
    {
        "form_number": "21-4138",
        "title": "Statement in Support of Claim",
        "category": "evidence",
        "url": "https://www.va.gov/find-forms/about-form-21-4138/",
        "guidance": "Lay statements and buddy statements often use this form.",
    },
    {
        "form_number": "20-0995",
        "title": "Decision Review Request: Supplemental Claim",
        "category": "appeals",
        "guidance": "New and relevant evidence path. Not legal advice.",
    },
    {
        "form_number": "20-0996",
        "title": "Decision Review Request: Higher-Level Review",
        "category": "appeals",
        "guidance": "Same evidence, senior reviewer. Seek accredited help for complex cases.",
    },
]


def _ensure_forms(db: Session) -> None:
    if db.query(VaForm).count() == 0:
        for f in DEFAULT_FORMS:
            db.add(VaForm(**f))
        db.commit()


@router.get("/forms", response_model=list[VaFormOut])
def list_forms(db: Session = Depends(get_db)):
    _ensure_forms(db)
    return db.query(VaForm).order_by(VaForm.form_number).all()


@router.get("/forms/{form_id}", response_model=VaFormOut)
def get_form(form_id: UUID, db: Session = Depends(get_db)):
    _ensure_forms(db)
    form = db.query(VaForm).filter(VaForm.id == form_id).first()
    if form is None:
        # also allow lookup by form number via path misuse fallback
        form = db.query(VaForm).filter(VaForm.form_number == str(form_id)).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Form not found")
    return form


@router.get("/intent-to-file/checklist")
def itf_checklist():
    return intent_to_file_checklist()
