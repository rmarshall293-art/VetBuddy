"""SQLAlchemy ORM models — canonical VetBuddy schema."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class GUID(TypeDecorator):
    """Platform-independent UUID — stored as native UUID on Postgres, string on SQLite."""

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


JSONType = JSON().with_variant(JSONB(), "postgresql")


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="role")


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret_encrypted: Mapped[Optional[str]] = mapped_column(String(512))
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(64))
    oauth_subject: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    profile: Mapped[Optional["UserProfile"]] = relationship(back_populates="user", uselist=False)
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="user")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    claims: Mapped[list["Claim"]] = relationship(back_populates="user")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(200))
    preferred_jurisdiction: Mapped[Optional[str]] = mapped_column(String(8))
    service_branch: Mapped[Optional[str]] = mapped_column(String(64))
    service_era: Mapped[Optional[str]] = mapped_column(String(64))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    city: Mapped[Optional[str]] = mapped_column(String(120))
    state: Mapped[Optional[str]] = mapped_column(String(8))
    zip_code: Mapped[Optional[str]] = mapped_column(String(16))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    # PII minimization: avoid SSN/DOB storage unless explicitly required later
    preferences: Mapped[Optional[dict]] = mapped_column(JSONType, default=dict)

    user: Mapped["User"] = relationship(back_populates="profile")


class UserRole(Base, TimestampMixin):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="user_roles")
    role: Mapped["Role"] = relationship(back_populates="user_roles")


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    refresh_token_jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    user_agent: Mapped[Optional[str]] = mapped_column(String(512))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))

    user: Mapped["User"] = relationship(back_populates="sessions")


class Organization(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    org_type: Mapped[str] = mapped_column(String(64), default="american_legion_post")
    jurisdiction_code: Mapped[Optional[str]] = mapped_column(String(8))
    external_ref: Mapped[Optional[str]] = mapped_column(String(128))


class Claim(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="draft", index=True)
    claim_type: Mapped[str] = mapped_column(String(64), default="disability")
    va_file_number_masked: Mapped[Optional[str]] = mapped_column(String(32))
    intent_to_file_date: Mapped[Optional[date]] = mapped_column(Date)
    evidence_strength_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    missing_evidence_warnings: Mapped[Optional[dict]] = mapped_column(JSONType, default=list)
    appeal_path: Mapped[Optional[str]] = mapped_column(String(64))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    disclaimer_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="claims")
    conditions: Mapped[list["ClaimCondition"]] = relationship(back_populates="claim")
    evidence: Mapped[list["ClaimEvidence"]] = relationship(back_populates="claim")


class ClaimCondition(Base, TimestampMixin):
    __tablename__ = "claim_conditions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    condition_name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    in_service_event: Mapped[Optional[str]] = mapped_column(Text)
    nexus_evidence: Mapped[Optional[str]] = mapped_column(Text)
    current_symptoms: Mapped[Optional[str]] = mapped_column(Text)
    treatment_history: Mapped[Optional[str]] = mapped_column(Text)
    diagnostic_code: Mapped[Optional[str]] = mapped_column(String(32))
    claimed_rating: Mapped[Optional[int]] = mapped_column(Integer)

    claim: Mapped["Claim"] = relationship(back_populates="conditions")


class ClaimEvidence(Base, TimestampMixin):
    __tablename__ = "claim_evidence"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="needed")
    checklist_item: Mapped[Optional[str]] = mapped_column(String(128))
    strength_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), default=1)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("documents.id", ondelete="SET NULL")
    )

    claim: Mapped["Claim"] = relationship(back_populates="evidence")


class Document(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(128))
    storage_key: Mapped[Optional[str]] = mapped_column(String(512))
    sha256: Mapped[Optional[str]] = mapped_column(String(64))
    meta: Mapped[Optional[dict]] = mapped_column(JSONType, default=dict)


class VaForm(Base, TimestampMixin):
    __tablename__ = "va_forms"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    form_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String(512))
    category: Mapped[Optional[str]] = mapped_column(String(64))
    guidance: Mapped[Optional[str]] = mapped_column(Text)


class IntentToFileRecord(Base, TimestampMixin):
    __tablename__ = "intent_to_file_records"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("claims.id", ondelete="SET NULL")
    )
    filed_date: Mapped[Optional[date]] = mapped_column(Date)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="planned")
    notes: Mapped[Optional[str]] = mapped_column(Text)


class Benefit(Base, TimestampMixin):
    __tablename__ = "benefits"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(128), index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    eligibility: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(128))
    url: Mapped[Optional[str]] = mapped_column(String(512))
    jurisdiction_code: Mapped[Optional[str]] = mapped_column(String(8), index=True)
    data_status: Mapped[str] = mapped_column(String(32), default="placeholder")


class Jurisdiction(Base, TimestampMixin):
    __tablename__ = "jurisdictions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    jurisdiction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    veteran_population: Mapped[Optional[int]] = mapped_column(Integer)
    cost_of_living_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    housing_affordability_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    unemployment_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    military_retirement_tax_rule: Mapped[Optional[str]] = mapped_column(Text)
    va_disability_tax_rule: Mapped[Optional[str]] = mapped_column(Text)
    property_tax_benefits_summary: Mapped[Optional[str]] = mapped_column(Text)
    education_benefits_summary: Mapped[Optional[str]] = mapped_column(Text)
    veterans_home_summary: Mapped[Optional[str]] = mapped_column(Text)
    healthcare_access_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    gi_bill_usage_metric: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    state_veterans_agency_name: Mapped[Optional[str]] = mapped_column(String(255))
    state_veterans_agency_url: Mapped[Optional[str]] = mapped_column(String(512))
    last_reviewed: Mapped[Optional[date]] = mapped_column(Date)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3))
    citations: Mapped[Optional[dict]] = mapped_column(JSONType, default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    data_status: Mapped[str] = mapped_column(String(32), default="placeholder")
    ranking_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    payload: Mapped[Optional[dict]] = mapped_column(JSONType, default=dict)


class JurisdictionBenefit(Base, TimestampMixin):
    __tablename__ = "jurisdiction_benefits"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("jurisdictions.id", ondelete="CASCADE"), nullable=False
    )
    benefit_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("benefits.id", ondelete="CASCADE"), nullable=False
    )
    details: Mapped[Optional[str]] = mapped_column(Text)


class StateTaxRule(Base, TimestampMixin):
    __tablename__ = "state_tax_rules"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    jurisdiction_code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    va_disability_tax_treatment: Mapped[Optional[str]] = mapped_column(Text)
    military_retirement_tax_treatment: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    data_status: Mapped[str] = mapped_column(String(32), default="placeholder")


class VaRateTable(Base, TimestampMixin):
    __tablename__ = "va_rate_tables"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    fiscal_year: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    rating_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    dependent_status: Mapped[str] = mapped_column(String(64), default="veteran_alone")
    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    data_status: Mapped[str] = mapped_column(String(32), default="placeholder")


class ColaTable(Base, TimestampMixin):
    __tablename__ = "cola_tables"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    year: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    cola_percent: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)


class Facility(Base, TimestampMixin):
    __tablename__ = "facilities"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    facility_type: Mapped[str] = mapped_column(String(64))
    jurisdiction_code: Mapped[Optional[str]] = mapped_column(String(8), index=True)
    city: Mapped[Optional[str]] = mapped_column(String(120))
    address: Mapped[Optional[str]] = mapped_column(String(512))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    url: Mapped[Optional[str]] = mapped_column(String(512))
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    meta: Mapped[Optional[dict]] = mapped_column(JSONType, default=dict)
    data_status: Mapped[str] = mapped_column(String(32), default="placeholder")


class ResourceOfficerAssignment(Base, TimestampMixin):
    __tablename__ = "resource_officer_assignments"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    officer_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    veteran_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("organizations.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(32), default="active")


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(64))
    resource_id: Mapped[Optional[str]] = mapped_column(String(64))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    request_id: Mapped[Optional[str]] = mapped_column(String(64))
    details: Mapped[Optional[dict]] = mapped_column(JSONType, default=dict)
    # Never store sensitive VA API payloads here — metadata only


class ApiIntegrationLog(Base, TimestampMixin):
    __tablename__ = "api_integration_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    request_id: Mapped[Optional[str]] = mapped_column(String(64))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSONType, default=dict)
    # Session-only: do not persist VA tokens or full PHI payloads


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(128))
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    tier: Mapped[str] = mapped_column(String(64), default="free")
    status: Mapped[str] = mapped_column(String(64), default="inactive")
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # Tiers: free | consumer ($5.99/mo) | resource_officer | admin
    # Apple/Google billing placeholders for future mobile apps
    apple_original_transaction_id: Mapped[Optional[str]] = mapped_column(String(128))
    google_purchase_token: Mapped[Optional[str]] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="subscriptions")


class PaymentEvent(Base, TimestampMixin):
    __tablename__ = "payment_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL")
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("subscriptions.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    stripe_event_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    amount_cents: Mapped[Optional[int]] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="usd")
    payload_summary: Mapped[Optional[dict]] = mapped_column(JSONType, default=dict)


class SecurityChecklistItem(Base, TimestampMixin):
    __tablename__ = "security_checklist"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="not_started")
    owner: Mapped[Optional[str]] = mapped_column(String(128))
    evidence_url: Mapped[Optional[str]] = mapped_column(String(512))
    notes: Mapped[Optional[str]] = mapped_column(Text)


class LegalReadinessItem(Base, TimestampMixin):
    __tablename__ = "legal_readiness_checklist"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="not_started")
    # Tracks SDVOSB, SAM.gov, UEI, CAGE, insurance, privacy, ToS, DSA — not certifications
    value: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)


class LoadTestResult(Base, TimestampMixin):
    __tablename__ = "load_test_results"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    run_name: Mapped[str] = mapped_column(String(128), nullable=False)
    tool: Mapped[str] = mapped_column(String(32), default="locust")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    concurrent_users: Mapped[Optional[int]] = mapped_column(Integer)
    total_requests: Mapped[Optional[int]] = mapped_column(Integer)
    failure_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3))
    p95_latency_ms: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    report: Mapped[Optional[dict]] = mapped_column(JSONType, default=dict)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), default="general")
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class SavedStateComparison(Base, TimestampMixin):
    __tablename__ = "saved_state_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_code: Mapped[str] = mapped_column(String(8), nullable=False)
    to_code: Mapped[str] = mapped_column(String(8), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(128))
    metrics_filter: Mapped[Optional[dict]] = mapped_column(JSONType, default=list)
    snapshot: Mapped[Optional[dict]] = mapped_column(JSONType, default=dict)


class AlabamaRankingMetric(Base, TimestampMixin):
    __tablename__ = "alabama_ranking_metrics"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    metric_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    alabama_value: Mapped[Optional[str]] = mapped_column(String(255))
    national_rank: Mapped[Optional[int]] = mapped_column(Integer)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    # WalletHub-style ranking placeholder — clearly educational/placeholder
    wallethub_placeholder_rank: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    data_status: Mapped[str] = mapped_column(String(32), default="placeholder")
    citations: Mapped[Optional[dict]] = mapped_column(JSONType, default=list)
