"""Admin checklist and load-test result routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.rbac import require_admin
from app.db.database import get_db
from app.db.models import (
    LegalReadinessItem,
    LoadTestResult,
    SecurityChecklistItem,
    User,
)
from app.db.schemas import ChecklistItemOut, ChecklistUpdate, LoadTestResultOut

router = APIRouter(prefix="/admin", tags=["admin"])


DEFAULT_SECURITY = [
    ("owasp_injection", "OWASP A03 Injection protections reviewed"),
    ("encryption_transit", "TLS encryption in transit enforced"),
    ("encryption_rest", "Encryption at rest assumptions documented"),
    ("rls_enabled", "Postgres RLS policies applied"),
    ("audit_logging", "Audit logging enabled for sensitive actions"),
    ("secrets_mgmt", "Secrets managed via environment / vault — not hardcoded"),
    ("pen_test", "Third-party penetration test scheduled/completed"),
    ("access_review", "Least-privilege access review completed"),
]

DEFAULT_LEGAL = [
    ("sdvosb", "SDVOSB certification status tracked"),
    ("sam_gov", "SAM.gov registration"),
    ("uei", "Unique Entity Identifier (UEI)"),
    ("cage", "CAGE code"),
    ("state_contracting", "State contracting readiness"),
    ("federal_contracting", "Federal contracting readiness"),
    ("insurance", "Insurance checklist"),
    ("privacy_policy", "Privacy policy checklist"),
    ("terms_of_service", "Terms of service checklist"),
    ("data_sharing", "Data-sharing agreement checklist"),
]


def _ensure_checklists(db: Session) -> None:
    if db.query(SecurityChecklistItem).count() == 0:
        for code, title in DEFAULT_SECURITY:
            db.add(SecurityChecklistItem(code=code, title=title, status="not_started"))
    if db.query(LegalReadinessItem).count() == 0:
        for code, title in DEFAULT_LEGAL:
            db.add(LegalReadinessItem(code=code, title=title, status="not_started"))
    db.commit()


@router.get("/security-checklist", response_model=list[ChecklistItemOut])
def security_checklist(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    _ensure_checklists(db)
    return db.query(SecurityChecklistItem).order_by(SecurityChecklistItem.code).all()


@router.patch("/security-checklist/{item_id}", response_model=ChecklistItemOut)
def update_security_item(
    item_id: UUID,
    payload: ChecklistUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    item = db.query(SecurityChecklistItem).filter(SecurityChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        if hasattr(item, k):
            setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.get("/legal-readiness", response_model=list[ChecklistItemOut])
def legal_readiness(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    _ensure_checklists(db)
    rows = db.query(LegalReadinessItem).order_by(LegalReadinessItem.code).all()
    return [
        ChecklistItemOut(
            id=r.id,
            code=r.code,
            title=r.title,
            description=r.description,
            status=r.status,
            notes=r.notes,
            value=r.value,
        )
        for r in rows
    ]


@router.patch("/legal-readiness/{item_id}", response_model=ChecklistItemOut)
def update_legal_item(
    item_id: UUID,
    payload: ChecklistUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    item = db.query(LegalReadinessItem).filter(LegalReadinessItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        if hasattr(item, k):
            setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return ChecklistItemOut(
        id=item.id,
        code=item.code,
        title=item.title,
        description=item.description,
        status=item.status,
        notes=item.notes,
        value=item.value,
    )


@router.get("/load-test-results", response_model=list[LoadTestResultOut])
def load_test_results(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(LoadTestResult).order_by(LoadTestResult.created_at.desc()).limit(50).all()
