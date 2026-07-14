"""VA mock / sandbox provider — used when live Lighthouse credentials are absent."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from uuid import uuid4


def mock_veteran_profile() -> dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": "mock-veteran-001",
        "data_status": "mock",
        "name": [{"text": "Demo Veteran One"}],
        "gender": "unknown",
        "birthDate": None,  # PII minimization — not provided in mock
        "meta": {
            "source": "va_mock",
            "note": "Synthetic FHIR-shaped profile for local development only",
        },
        "extension": [
            {"url": "http://vetbuddy.local/fhir/service-branch", "valueString": "Army"},
            {"url": "http://vetbuddy.local/fhir/preferred-jurisdiction", "valueString": "AL"},
        ],
    }


def mock_claims() -> list[dict[str, Any]]:
    return [
        {
            "id": "mock-claim-1001",
            "type": "Compensation",
            "status": "PENDING",
            "dateFiled": (date.today() - timedelta(days=45)).isoformat(),
            "contentionList": ["Tinnitus", "Lumbar strain"],
            "data_status": "mock",
        },
        {
            "id": "mock-claim-1002",
            "type": "Compensation",
            "status": "EVIDENCE_GATHERING",
            "dateFiled": (date.today() - timedelta(days=120)).isoformat(),
            "contentionList": ["PTSD"],
            "data_status": "mock",
        },
    ]


def mock_lighthouse_session() -> dict[str, Any]:
    state = uuid4().hex
    return {
        "authorization_url": f"https://sandbox-api.va.gov/oauth2/authorization?mock=1&state={state}",
        "state": state,
        "expires_in": 600,
        "mock": True,
        "note": (
            "Mock VA Lighthouse session. Register at https://developer.va.gov "
            "and set VA_CLIENT_ID / VA_CLIENT_SECRET to enable live sandbox OAuth. "
            "Do not permanently store access tokens."
        ),
    }
