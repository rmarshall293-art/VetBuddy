"""Pydantic v2 request/response schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Auth ----
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: Optional[str] = None
    role: str = "veteran"
    preferred_jurisdiction: Optional[str] = "AL"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str


# ---- Users ----
class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    preferred_jurisdiction: Optional[str] = None
    service_branch: Optional[str] = None
    service_era: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    bio: Optional[str] = None


class UserProfileOut(ORMModel):
    id: UUID
    display_name: Optional[str] = None
    preferred_jurisdiction: Optional[str] = None
    service_branch: Optional[str] = None
    service_era: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    bio: Optional[str] = None


class UserOut(ORMModel):
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    roles: list[str] = []
    profile: Optional[UserProfileOut] = None
    created_at: Optional[datetime] = None


# ---- Claims ----
class ClaimConditionIn(BaseModel):
    condition_name: str
    current_diagnosis: Optional[str] = None
    in_service_event: Optional[str] = None
    nexus_evidence: Optional[str] = None
    current_symptoms: Optional[str] = None
    treatment_history: Optional[str] = None
    diagnostic_code: Optional[str] = None
    claimed_rating: Optional[int] = None


class ClaimConditionOut(ClaimConditionIn, ORMModel):
    id: UUID


class ClaimCreate(BaseModel):
    title: str
    claim_type: str = "disability"
    status: str = "draft"
    intent_to_file_date: Optional[date] = None
    notes: Optional[str] = None
    disclaimer_acknowledged: bool = False
    conditions: list[ClaimConditionIn] = []


class ClaimUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    claim_type: Optional[str] = None
    intent_to_file_date: Optional[date] = None
    notes: Optional[str] = None
    appeal_path: Optional[str] = None
    disclaimer_acknowledged: Optional[bool] = None


class EvidenceCreate(BaseModel):
    evidence_type: str
    title: str
    description: Optional[str] = None
    status: str = "needed"
    checklist_item: Optional[str] = None
    strength_weight: Optional[Decimal] = Decimal("1.0")


class EvidenceOut(EvidenceCreate, ORMModel):
    id: UUID
    claim_id: UUID


class ClaimOut(ORMModel):
    id: UUID
    title: str
    status: str
    claim_type: str
    intent_to_file_date: Optional[date] = None
    evidence_strength_score: Optional[Decimal] = None
    missing_evidence_warnings: Optional[Any] = None
    appeal_path: Optional[str] = None
    notes: Optional[str] = None
    disclaimer_acknowledged: bool = False
    conditions: list[ClaimConditionOut] = []
    evidence: list[EvidenceOut] = []
    created_at: Optional[datetime] = None


# ---- Forms / Benefits ----
class VaFormOut(ORMModel):
    id: UUID
    form_number: str
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    guidance: Optional[str] = None


class BenefitOut(ORMModel):
    id: UUID
    name: str
    category: str
    summary: Optional[str] = None
    eligibility: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    jurisdiction_code: Optional[str] = None
    data_status: str = "placeholder"


# ---- State comparison ----
class JurisdictionOut(ORMModel):
    id: UUID
    code: str
    name: str
    jurisdiction_type: str
    veteran_population: Optional[int] = None
    cost_of_living_index: Optional[Decimal] = None
    housing_affordability_index: Optional[Decimal] = None
    unemployment_rate: Optional[Decimal] = None
    military_retirement_tax_rule: Optional[str] = None
    va_disability_tax_rule: Optional[str] = None
    property_tax_benefits_summary: Optional[str] = None
    education_benefits_summary: Optional[str] = None
    veterans_home_summary: Optional[str] = None
    healthcare_access_score: Optional[Decimal] = None
    gi_bill_usage_metric: Optional[Decimal] = None
    state_veterans_agency_name: Optional[str] = None
    state_veterans_agency_url: Optional[str] = None
    last_reviewed: Optional[date] = None
    confidence_score: Optional[Decimal] = None
    citations: Optional[Any] = None
    notes: Optional[str] = None
    data_status: str = "placeholder"
    ranking_score: Optional[Decimal] = None


class ComparisonResult(BaseModel):
    from_jurisdiction: JurisdictionOut
    to_jurisdiction: JurisdictionOut
    metrics: dict[str, Any]
    placeholder_warning: bool = True
    alabama_quick_compare: Optional[dict[str, Any]] = None


class CustomCompareRequest(BaseModel):
    from_code: str
    to_code: str
    metrics: list[str] = []
    save: bool = False
    label: Optional[str] = None


# ---- Payments ----
class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str
    mock: bool = False


class SubscriptionStatus(BaseModel):
    tier: str
    status: str
    current_period_end: Optional[datetime] = None
    price_cents: int = 599


# ---- Admin ----
class ChecklistItemOut(ORMModel):
    id: UUID
    code: str
    title: str
    description: Optional[str] = None
    status: str
    notes: Optional[str] = None
    value: Optional[str] = None


class ChecklistUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    value: Optional[str] = None
    evidence_url: Optional[str] = None


class LoadTestResultOut(ORMModel):
    id: UUID
    run_name: str
    tool: str
    concurrent_users: Optional[int] = None
    total_requests: Optional[int] = None
    failure_rate: Optional[Decimal] = None
    p95_latency_ms: Optional[Decimal] = None
    notes: Optional[str] = None
    report: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    va_mode: str
    stripe_mode: str
