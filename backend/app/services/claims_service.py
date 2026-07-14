"""Claims analysis service with evidence scoring and educational disclaimers."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.models import Claim, ClaimCondition, ClaimEvidence, User
from app.db.schemas import ClaimCreate, ClaimUpdate, EvidenceCreate

DISCLAIMER = (
    "VetBuddy provides educational guidance and organization support only. "
    "It is not legal advice and does not provide accredited representation before the VA. "
    "Consult an accredited VSO, attorney, or claims agent for formal representation."
)

EVIDENCE_CHECKLIST = [
    "lay_statement",
    "buddy_statement",
    "medical_records",
    "nexus_letter",
    "dd214",
    "treatment_history",
]

APPEAL_PATHS = {
    "supplemental": "Supplemental Claim — new and relevant evidence path",
    "higher_level_review": "Higher-Level Review — same evidence, senior reviewer",
    "board": "Board of Veterans' Appeals — education path only; seek accredited help",
}


def list_claims(db: Session, user: User) -> list[Claim]:
    return (
        db.query(Claim)
        .options(joinedload(Claim.conditions), joinedload(Claim.evidence))
        .filter(Claim.user_id == user.id, Claim.deleted_at.is_(None))
        .order_by(Claim.created_at.desc())
        .all()
    )


def get_claim(db: Session, user: User, claim_id: UUID) -> Claim:
    claim = (
        db.query(Claim)
        .options(joinedload(Claim.conditions), joinedload(Claim.evidence))
        .filter(Claim.id == claim_id, Claim.user_id == user.id, Claim.deleted_at.is_(None))
        .first()
    )
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim


def create_claim(db: Session, user: User, payload: ClaimCreate) -> Claim:
    claim = Claim(
        user_id=user.id,
        title=payload.title,
        claim_type=payload.claim_type,
        status=payload.status,
        intent_to_file_date=payload.intent_to_file_date,
        notes=payload.notes,
        disclaimer_acknowledged=payload.disclaimer_acknowledged,
        missing_evidence_warnings=list(EVIDENCE_CHECKLIST),
    )
    db.add(claim)
    db.flush()
    for cond in payload.conditions:
        db.add(ClaimCondition(claim_id=claim.id, **cond.model_dump()))
    _recompute_evidence_score(db, claim)
    db.commit()
    return get_claim(db, user, claim.id)


def update_claim(db: Session, user: User, claim_id: UUID, payload: ClaimUpdate) -> Claim:
    claim = get_claim(db, user, claim_id)
    data = payload.model_dump(exclude_unset=True)
    if "appeal_path" in data and data["appeal_path"] and data["appeal_path"] not in APPEAL_PATHS:
        raise HTTPException(status_code=400, detail=f"appeal_path must be one of {list(APPEAL_PATHS)}")
    for key, value in data.items():
        setattr(claim, key, value)
    db.commit()
    return get_claim(db, user, claim.id)


def delete_claim(db: Session, user: User, claim_id: UUID) -> None:
    from datetime import datetime, timezone

    claim = get_claim(db, user, claim_id)
    claim.deleted_at = datetime.now(timezone.utc)
    db.commit()


def add_evidence(db: Session, user: User, claim_id: UUID, payload: EvidenceCreate) -> ClaimEvidence:
    claim = get_claim(db, user, claim_id)
    evidence = ClaimEvidence(claim_id=claim.id, **payload.model_dump())
    db.add(evidence)
    db.flush()
    _recompute_evidence_score(db, claim)
    db.commit()
    db.refresh(evidence)
    return evidence


def list_evidence(db: Session, user: User, claim_id: UUID) -> list[ClaimEvidence]:
    claim = get_claim(db, user, claim_id)
    return claim.evidence


def _recompute_evidence_score(db: Session, claim: Claim) -> None:
    items = db.query(ClaimEvidence).filter(ClaimEvidence.claim_id == claim.id).all()
    present_types = {e.checklist_item or e.evidence_type for e in items if e.status != "needed"}
    missing = [c for c in EVIDENCE_CHECKLIST if c not in present_types]
    total_weight = sum(float(e.strength_weight or 1) for e in items if e.status != "needed")
    score = min(Decimal("100"), Decimal(str(round(total_weight * 12.5, 2))))
    claim.evidence_strength_score = score
    claim.missing_evidence_warnings = missing


def intent_to_file_checklist() -> dict:
    return {
        "disclaimer": DISCLAIMER,
        "steps": [
            {
                "id": 1,
                "title": "Confirm eligibility path",
                "detail": "Identify disability, pension, or survivor claim intent.",
            },
            {
                "id": 2,
                "title": "Submit Intent to File (VA Form 21-0966)",
                "detail": "Preserves effective date for up to one year while gathering evidence.",
            },
            {
                "id": 3,
                "title": "Create or verify VA.gov account",
                "detail": "Use Login.gov or ID.me; never share credentials with VetBuddy.",
            },
            {
                "id": 4,
                "title": "Gather DD214 and medical evidence",
                "detail": "Service treatment records, private medical, nexus support.",
            },
            {
                "id": 5,
                "title": "Consult accredited VSO/resource officer",
                "detail": "Especially recommended for Alabama pilot posts and county VSOs.",
            },
        ],
        "reminders": [
            "ITF typically expires one year after submission.",
            "Educational guidance only — not legal representation.",
        ],
    }
