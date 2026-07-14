"""Alabama veteran resources and resource-officer training module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AlabamaRankingMetric, Facility

def _resolve_data_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parents[3] / "data",
        Path(__file__).resolve().parents[2] / "data",
        Path("/app/data"),
        Path("/workspace/data"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


DATA_DIR = _resolve_data_dir()


def _load(name: str) -> Any:
    path = DATA_DIR / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def get_alabama_benefits() -> list[dict]:
    return _load("alabama_benefits.json")


def get_county_offices(db: Session) -> list[dict]:
    facilities = (
        db.query(Facility)
        .filter(Facility.jurisdiction_code == "AL")
        .order_by(Facility.name)
        .all()
    )
    if facilities:
        return [
            {
                "id": str(f.id),
                "name": f.name,
                "facility_type": f.facility_type,
                "city": f.city,
                "address": f.address,
                "phone": f.phone,
                "url": f.url,
                "data_status": f.data_status,
            }
            for f in facilities
        ]
    mock = _load("facilities_mock.json")
    if isinstance(mock, dict):
        return mock.get("facilities", mock.get("items", []))
    return mock


TRAINING_LEVELS = {
    "level_1": {
        "title": "Basic Veteran Resource Officer",
        "modules": [
            "Veteran intake",
            "VA.gov account creation guidance",
            "Intent to file",
            "Evidence gathering",
            "DD214 review",
            "VA forms overview",
            "Alabama benefits overview",
            "Referral to accredited VSO",
        ],
        "quiz": [
            {
                "q": "Who may provide accredited VA representation?",
                "choices": ["Any volunteer", "Accredited VSO/attorney/claims agent", "Family only"],
                "answer": 1,
            },
            {
                "q": "Intent to File primarily preserves which date?",
                "choices": ["Discharge date", "Potential effective date", "Court date"],
                "answer": 1,
            },
        ],
    },
    "level_2": {
        "title": "Claims Support Assistant",
        "modules": [
            "Claim condition organization",
            "Medical evidence checklist",
            "Lay statement guidance",
            "Buddy statement guidance",
            "Tracking claim status",
            "Survivor/death benefits overview",
            "Education benefits overview",
        ],
        "quiz": [
            {
                "q": "A nexus letter typically connects:",
                "choices": ["Tax records", "In-service event to current disability", "Housing vouchers"],
                "answer": 1,
            }
        ],
    },
    "level_3": {
        "title": "Department Resource Coordinator",
        "modules": [
            "Post-level reporting",
            "County office coordination",
            "ADVA coordination",
            "American Legion Department support",
            "Training compliance",
            "Audit trail",
            "Escalation workflow",
        ],
        "quiz": [
            {
                "q": "Escalation for complex claims should go to:",
                "choices": ["Social media", "Accredited representative / ADVA pathways", "Anonymous forums"],
                "answer": 1,
            }
        ],
    },
}


def resource_officer_training() -> dict:
    return {
        "jurisdiction": "AL",
        "organization": "American Legion Department of Alabama — Post Resource Officer pathway",
        "disclaimer": (
            "Training prepares resource officers for education and navigation support. "
            "It does not confer VA accreditation."
        ),
        "levels": TRAINING_LEVELS,
        "completion_tracking": {
            "storage": "Track completions via user preferences / notifications in a future release",
            "checklists": True,
            "quizzes": True,
        },
    }


def alabama_ranking(db: Session) -> dict:
    rows = db.query(AlabamaRankingMetric).order_by(AlabamaRankingMetric.national_rank.nulls_last()).all()
    metrics = [
        {
            "metric_key": r.metric_key,
            "title": r.title,
            "alabama_value": r.alabama_value,
            "national_rank": r.national_rank,
            "score": float(r.score) if r.score is not None else None,
            "wallethub_placeholder_rank": r.wallethub_placeholder_rank,
            "notes": r.notes,
            "data_status": r.data_status,
            "citations": r.citations,
        }
        for r in rows
    ]
    if not metrics:
        metrics = [
            {
                "metric_key": "overall_placeholder",
                "title": "Overall veteran friendliness (placeholder)",
                "alabama_value": "Competitive — pilot focus",
                "national_rank": None,
                "score": 78.0,
                "wallethub_placeholder_rank": None,
                "notes": "WalletHub-style ranking placeholder only; not an official ranking.",
                "data_status": "placeholder",
                "citations": [],
            }
        ]
    return {
        "jurisdiction": "AL",
        "title": "Alabama competitive ranking analysis",
        "placeholder_warning": True,
        "metrics": metrics,
    }
