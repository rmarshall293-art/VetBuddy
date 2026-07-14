"""State comparison service for 56 jurisdictions."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Jurisdiction, SavedStateComparison, User

def _resolve_data_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parents[3] / "data",  # repo root (local)
        Path(__file__).resolve().parents[2] / "data",  # /app/data (Docker)
        Path("/app/data"),
        Path("/workspace/data"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


DATA_DIR = _resolve_data_dir()
JURISDICTIONS_FILE = DATA_DIR / "jurisdictions_56.json"

COMPARISON_METRICS = [
    "va_disability_tax_rule",
    "military_retirement_tax_rule",
    "property_tax_benefits_summary",
    "education_benefits_summary",
    "veterans_home_summary",
    "unemployment_rate",
    "gi_bill_usage_metric",
    "cost_of_living_index",
    "housing_affordability_index",
    "healthcare_access_score",
    "veteran_population",
    "state_veterans_agency_name",
    "state_veterans_agency_url",
    "ranking_score",
    "confidence_score",
]


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _load_json_fallback() -> list[dict[str, Any]]:
    if JURISDICTIONS_FILE.exists():
        raw = json.loads(JURISDICTIONS_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "jurisdictions" in raw:
            return raw["jurisdictions"]
        if isinstance(raw, list):
            return raw
    return []


def ensure_jurisdictions_seeded(db: Session) -> int:
    """Seed jurisdictions from JSON if table is empty."""
    count = db.query(Jurisdiction).count()
    if count > 0:
        return count
    rows = _load_json_fallback()
    for row in rows:
        db.add(
            Jurisdiction(
                code=row.get("abbreviation") or row.get("id"),
                name=row["name"],
                jurisdiction_type=row.get("type", "state"),
                veteran_population=row.get("veteran_population"),
                cost_of_living_index=row.get("cost_of_living_index"),
                housing_affordability_index=row.get("housing_affordability_index"),
                unemployment_rate=row.get("unemployment_rate"),
                military_retirement_tax_rule=row.get("military_retirement_tax_rule"),
                va_disability_tax_rule=row.get("va_disability_tax_rule"),
                property_tax_benefits_summary=row.get("property_tax_benefits_summary"),
                education_benefits_summary=row.get("education_benefits_summary"),
                veterans_home_summary=row.get("veterans_home_summary"),
                healthcare_access_score=row.get("healthcare_access_score"),
                gi_bill_usage_metric=row.get("gi_bill_usage_metric"),
                state_veterans_agency_name=row.get("state_veterans_agency_name"),
                state_veterans_agency_url=row.get("state_veterans_agency_url"),
                last_reviewed=_parse_date(row.get("last_reviewed")),
                confidence_score=row.get("confidence_score"),
                citations=row.get("citations"),
                notes=row.get("notes"),
                data_status=row.get("data_status", "placeholder"),
                ranking_score=row.get("ranking_score"),
                payload=row,
            )
        )
    db.commit()
    return len(rows)


def list_jurisdictions(db: Session) -> list[Jurisdiction]:
    ensure_jurisdictions_seeded(db)
    return db.query(Jurisdiction).order_by(Jurisdiction.name).all()


def get_jurisdiction(db: Session, jurisdiction_id: str) -> Jurisdiction:
    ensure_jurisdictions_seeded(db)
    # Accept UUID or abbreviation code
    q = db.query(Jurisdiction)
    try:
        uid = UUID(jurisdiction_id)
        row = q.filter(Jurisdiction.id == uid).first()
    except ValueError:
        row = q.filter(Jurisdiction.code == jurisdiction_id.upper()).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jurisdiction not found")
    return row


def compare(db: Session, from_code: str, to_code: str, metrics: Optional[list[str]] = None) -> dict:
    left = get_jurisdiction(db, from_code)
    right = get_jurisdiction(db, to_code)
    selected = metrics or COMPARISON_METRICS
    metric_map: dict[str, Any] = {}
    for key in selected:
        metric_map[key] = {
            "from": getattr(left, key, None) if hasattr(left, key) else (left.payload or {}).get(key),
            "to": getattr(right, key, None) if hasattr(right, key) else (right.payload or {}).get(key),
        }
    alabama = None
    if "AL" not in {from_code.upper(), to_code.upper()}:
        al = get_jurisdiction(db, "AL")
        alabama = {
            "code": "AL",
            "name": al.name,
            "ranking_score": float(al.ranking_score or 0),
            "note": "Alabama pilot competitive ranking snapshot",
        }
    return {
        "from_jurisdiction": left,
        "to_jurisdiction": right,
        "metrics": metric_map,
        "placeholder_warning": True,
        "alabama_quick_compare": alabama,
        "citations": {
            "from": left.citations,
            "to": right.citations,
        },
        "confidence": {
            "from": float(left.confidence_score or 0),
            "to": float(right.confidence_score or 0),
        },
    }


def save_comparison(
    db: Session,
    user: User,
    from_code: str,
    to_code: str,
    label: Optional[str],
    metrics: list[str],
    snapshot: dict,
) -> SavedStateComparison:
    row = SavedStateComparison(
        user_id=user.id,
        from_code=from_code.upper(),
        to_code=to_code.upper(),
        label=label,
        metrics_filter=metrics,
        snapshot=snapshot,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
