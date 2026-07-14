-- =============================================================================
-- VetBuddy Canonical PostgreSQL Schema
-- =============================================================================
-- Purpose: Single source of truth for the VetBuddy veteran support platform.
-- Target: PostgreSQL 14+ (Supabase-compatible).
-- Notes:
--   - UUID primary keys via pgcrypto (gen_random_uuid).
--   - Application-layer authorization is enforced by FastAPI; RLS (see
--     rls_policies.sql) provides defense-in-depth for direct Postgres access.
--   - Soft-delete via deleted_at on users, claims, documents, organizations.
-- =============================================================================

-- Extensions ------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

COMMENT ON EXTENSION pgcrypto IS 'Cryptographic functions including gen_random_uuid()';
COMMENT ON EXTENSION "uuid-ossp" IS 'Legacy UUID generation fallback (uuid_generate_v4)';

-- Shared trigger: maintain updated_at -----------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION set_updated_at() IS 'Trigger function to auto-set updated_at on row update';

-- =============================================================================
-- CORE IDENTITY
-- =============================================================================

-- users: authentication identity, MFA, OAuth, billing linkage
CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(320) NOT NULL,
    password_hash       VARCHAR(255),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    -- MFA-ready fields (TOTP secret stored encrypted at rest by the app layer)
    mfa_enabled         BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret_encrypted TEXT,
    -- OAuth provider linkage (nullable for password-only accounts)
    oauth_provider      VARCHAR(64),
    oauth_subject       VARCHAR(255),
    -- Stripe customer ID for subscription billing
    stripe_customer_id  VARCHAR(255),
    last_login_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT users_email_unique UNIQUE (email)
);

COMMENT ON TABLE users IS 'Platform user accounts with auth, MFA, OAuth, and billing identifiers';
COMMENT ON COLUMN users.password_hash IS 'bcrypt hash; NULL for OAuth-only accounts';
COMMENT ON COLUMN users.mfa_secret_encrypted IS 'AES-256-GCM encrypted TOTP secret; app-layer key required';
COMMENT ON COLUMN users.oauth_provider IS 'e.g. google, apple, va_lighthouse';
COMMENT ON COLUMN users.oauth_subject IS 'Provider-specific subject / sub claim';
COMMENT ON COLUMN users.stripe_customer_id IS 'Stripe cus_* identifier for payment management';
COMMENT ON COLUMN users.deleted_at IS 'Soft-delete timestamp; active users have NULL deleted_at';

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- OAuth provider+subject must be unique when set (password-only users may have NULLs)
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_oauth_provider_subject
    ON users (oauth_provider, oauth_subject)
    WHERE oauth_provider IS NOT NULL AND oauth_subject IS NOT NULL;

-- user_profiles: PII and veteran-specific profile data (1:1 with users)
CREATE TABLE IF NOT EXISTS user_profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_name              VARCHAR(100),
    last_name               VARCHAR(100),
    middle_name             VARCHAR(100),
    phone                   VARCHAR(32),
    date_of_birth           DATE,
    address_line1           VARCHAR(255),
    address_line2           VARCHAR(255),
    city                    VARCHAR(100),
    state_code              CHAR(2),
    postal_code             VARCHAR(20),
    country_code            CHAR(2) NOT NULL DEFAULT 'US',
    branch_of_service       VARCHAR(64),
    service_start_date      DATE,
    service_end_date        DATE,
    discharge_type          VARCHAR(64),
    va_file_number_masked   VARCHAR(32),
    preferred_jurisdiction_id UUID,
    avatar_url              TEXT,
    bio                     TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT user_profiles_user_id_unique UNIQUE (user_id)
);

COMMENT ON TABLE user_profiles IS 'Extended profile and veteran service metadata (1:1 with users)';
COMMENT ON COLUMN user_profiles.va_file_number_masked IS 'Last-4 or masked VA file number; full number never stored in plaintext';

CREATE TRIGGER trg_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- roles: RBAC role catalog
CREATE TABLE IF NOT EXISTS roles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(64) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT roles_name_unique UNIQUE (name)
);

COMMENT ON TABLE roles IS 'Role catalog: veteran, family_member, vso_resource_officer, department_admin, super_admin, etc.';

-- organizations: VSOs, departments, partner orgs
CREATE TABLE IF NOT EXISTS organizations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    VARCHAR(255) NOT NULL,
    org_type                VARCHAR(64) NOT NULL,
    ein                     VARCHAR(20),
    uei                     VARCHAR(20),
    cage_code               VARCHAR(10),
    address_line1           VARCHAR(255),
    address_line2           VARCHAR(255),
    city                    VARCHAR(100),
    state_code              CHAR(2),
    postal_code             VARCHAR(20),
    contact_email           VARCHAR(320),
    contact_phone           VARCHAR(32),
    website_url             TEXT,
    parent_organization_id  UUID REFERENCES organizations(id),
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMPTZ
);

COMMENT ON TABLE organizations IS 'VSO, American Legion post, department, and partner organizations';
COMMENT ON COLUMN organizations.uei IS 'SAM.gov Unique Entity Identifier';
COMMENT ON COLUMN organizations.cage_code IS 'Commercial and Government Entity code';

CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- user_roles: many-to-many user ↔ role (optionally scoped to org)
CREATE TABLE IF NOT EXISTS user_roles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id         UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT user_roles_unique UNIQUE (user_id, role_id, organization_id)
);

COMMENT ON TABLE user_roles IS 'User role assignments; organization_id scopes department_admin and RO roles';

-- sessions: refresh-token / JWT session tracking
CREATE TABLE IF NOT EXISTS sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    jti                 VARCHAR(64) NOT NULL,
    refresh_token_hash  VARCHAR(255) NOT NULL,
    user_agent          TEXT,
    ip_address          INET,
    expires_at          TIMESTAMPTZ NOT NULL,
    revoked_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT sessions_jti_unique UNIQUE (jti)
);

COMMENT ON TABLE sessions IS 'Active refresh-token sessions keyed by JWT jti for rotation and revocation';
COMMENT ON COLUMN sessions.jti IS 'JWT ID claim; used for token revocation lookups';

-- =============================================================================
-- CLAIMS & DOCUMENTS
-- =============================================================================

-- claims: veteran disability / benefits claims
CREATE TABLE IF NOT EXISTS claims (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    claim_type          VARCHAR(64) NOT NULL DEFAULT 'initial',
    status              VARCHAR(64) NOT NULL DEFAULT 'draft',
    va_claim_id         VARCHAR(64),
    filing_date         DATE,
    decision_date       DATE,
    combined_rating     INTEGER CHECK (combined_rating IS NULL OR (combined_rating >= 0 AND combined_rating <= 100)),
    intent_to_file_id   UUID,
    notes               TEXT,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE claims IS 'Veteran disability and benefits claims tracked in VetBuddy';
COMMENT ON COLUMN claims.va_claim_id IS 'External VA claim identifier when synced via Lighthouse (mock in dev)';
COMMENT ON COLUMN claims.status IS 'draft, submitted, pending, decided, appealed, closed';

CREATE TRIGGER trg_claims_updated_at
    BEFORE UPDATE ON claims
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- claim_conditions: individual conditions within a claim
CREATE TABLE IF NOT EXISTS claim_conditions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id            UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    condition_name      VARCHAR(255) NOT NULL,
    diagnostic_code     VARCHAR(16),
    body_system         VARCHAR(64),
    claimed_rating      INTEGER CHECK (claimed_rating IS NULL OR (claimed_rating >= 0 AND claimed_rating <= 100)),
    granted_rating      INTEGER CHECK (granted_rating IS NULL OR (granted_rating >= 0 AND granted_rating <= 100)),
    status              VARCHAR(64) NOT NULL DEFAULT 'pending',
    onset_date          DATE,
    service_connection  BOOLEAN,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE claim_conditions IS 'Individual medical conditions asserted within a claim';

CREATE TRIGGER trg_claim_conditions_updated_at
    BEFORE UPDATE ON claim_conditions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- documents: uploaded files (medical records, forms, evidence)
CREATE TABLE IF NOT EXISTS documents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    claim_id            UUID REFERENCES claims(id) ON DELETE SET NULL,
    document_type       VARCHAR(64) NOT NULL,
    file_name           VARCHAR(512) NOT NULL,
    mime_type           VARCHAR(128),
    storage_path        TEXT NOT NULL,
    file_size_bytes     BIGINT,
    checksum_sha256     VARCHAR(64),
    is_sensitive        BOOLEAN NOT NULL DEFAULT TRUE,
    uploaded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE documents IS 'Uploaded documents stored in object storage; path references Supabase/S3 bucket';
COMMENT ON COLUMN documents.storage_path IS 'Object storage key, not a public URL';

CREATE TRIGGER trg_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- claim_evidence: links evidence to claims and conditions
CREATE TABLE IF NOT EXISTS claim_evidence (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id            UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    claim_condition_id  UUID REFERENCES claim_conditions(id) ON DELETE SET NULL,
    document_id         UUID REFERENCES documents(id) ON DELETE SET NULL,
    evidence_type       VARCHAR(64) NOT NULL,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    submitted_at        TIMESTAMPTZ,
    va_evidence_id      VARCHAR(64),
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE claim_evidence IS 'Evidence items supporting a claim, optionally linked to documents';

CREATE TRIGGER trg_claim_evidence_updated_at
    BEFORE UPDATE ON claim_evidence
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- va_forms: catalog of VA form templates
CREATE TABLE IF NOT EXISTS va_forms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_number     VARCHAR(32) NOT NULL,
    title           VARCHAR(512) NOT NULL,
    description     TEXT,
    version         VARCHAR(32),
    pdf_url         TEXT,
    category        VARCHAR(64),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT va_forms_number_version_unique UNIQUE (form_number, version)
);

COMMENT ON TABLE va_forms IS 'Catalog of VA forms (21-526EZ, 21-4138, etc.) for guided filing';

CREATE TRIGGER trg_va_forms_updated_at
    BEFORE UPDATE ON va_forms
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- intent_to_file_records: ITF tracking (1-year protection window)
CREATE TABLE IF NOT EXISTS intent_to_file_records (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    benefit_type        VARCHAR(64) NOT NULL,
    filed_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expiration_date     DATE NOT NULL,
    confirmation_number VARCHAR(64),
    status              VARCHAR(64) NOT NULL DEFAULT 'active',
    va_itf_id           VARCHAR(64),
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE intent_to_file_records IS 'Intent to File records preserving effective date for back-pay';

CREATE TRIGGER trg_intent_to_file_updated_at
    BEFORE UPDATE ON intent_to_file_records
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Add deferred FK from claims to intent_to_file_records
ALTER TABLE claims
    DROP CONSTRAINT IF EXISTS claims_intent_to_file_fk;
ALTER TABLE claims
    ADD CONSTRAINT claims_intent_to_file_fk
    FOREIGN KEY (intent_to_file_id) REFERENCES intent_to_file_records(id) ON DELETE SET NULL;

-- =============================================================================
-- BENEFITS & JURISDICTIONS
-- =============================================================================

-- benefits: federal and state benefit definitions
CREATE TABLE IF NOT EXISTS benefits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(64) NOT NULL,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    category        VARCHAR(64),
    is_federal      BOOLEAN NOT NULL DEFAULT FALSE,
    source_url      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT benefits_code_unique UNIQUE (code)
);

COMMENT ON TABLE benefits IS 'Benefit program definitions (federal VA and state-level)';

CREATE TRIGGER trg_benefits_updated_at
    BEFORE UPDATE ON benefits
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- jurisdictions: US states and territories
CREATE TABLE IF NOT EXISTS jurisdictions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(128) NOT NULL,
    abbreviation    CHAR(2) NOT NULL,
    fips_code       CHAR(2),
    is_state        BOOLEAN NOT NULL DEFAULT TRUE,
    is_territory    BOOLEAN NOT NULL DEFAULT FALSE,
    veteran_population_estimate INTEGER,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT jurisdictions_abbreviation_unique UNIQUE (abbreviation)
);

COMMENT ON TABLE jurisdictions IS 'US states and territories for benefits comparison and tax rules';

CREATE TRIGGER trg_jurisdictions_updated_at
    BEFORE UPDATE ON jurisdictions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Add deferred FK from user_profiles to jurisdictions
ALTER TABLE user_profiles
    DROP CONSTRAINT IF EXISTS user_profiles_jurisdiction_fk;
ALTER TABLE user_profiles
    ADD CONSTRAINT user_profiles_jurisdiction_fk
    FOREIGN KEY (preferred_jurisdiction_id) REFERENCES jurisdictions(id) ON DELETE SET NULL;

-- jurisdiction_benefits: state-specific benefit availability and amounts
CREATE TABLE IF NOT EXISTS jurisdiction_benefits (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id     UUID NOT NULL REFERENCES jurisdictions(id) ON DELETE CASCADE,
    benefit_id          UUID NOT NULL REFERENCES benefits(id) ON DELETE CASCADE,
    is_available        BOOLEAN NOT NULL DEFAULT TRUE,
    eligibility_notes   TEXT,
    amount_min_cents    INTEGER,
    amount_max_cents    INTEGER,
    effective_date      DATE,
    expiration_date     DATE,
    source_url          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT jurisdiction_benefits_unique UNIQUE (jurisdiction_id, benefit_id, effective_date)
);

COMMENT ON TABLE jurisdiction_benefits IS 'Mapping of benefits to jurisdictions with eligibility and amount ranges';

CREATE TRIGGER trg_jurisdiction_benefits_updated_at
    BEFORE UPDATE ON jurisdiction_benefits
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- state_tax_rules: military / VA disability tax treatment by state
CREATE TABLE IF NOT EXISTS state_tax_rules (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id             UUID NOT NULL REFERENCES jurisdictions(id) ON DELETE CASCADE,
    tax_year                    INTEGER NOT NULL,
    military_retirement_exempt  BOOLEAN NOT NULL DEFAULT FALSE,
    va_disability_exempt        BOOLEAN NOT NULL DEFAULT FALSE,
    partial_exemption_notes     TEXT,
    rules                       JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_url                  TEXT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT state_tax_rules_unique UNIQUE (jurisdiction_id, tax_year)
);

COMMENT ON TABLE state_tax_rules IS 'State income tax treatment for military retirement and VA disability pay';

CREATE TRIGGER trg_state_tax_rules_updated_at
    BEFORE UPDATE ON state_tax_rules
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- va_rate_tables: VA disability compensation rate schedules
CREATE TABLE IF NOT EXISTS va_rate_tables (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    effective_date          DATE NOT NULL,
    rating_percentage       INTEGER NOT NULL CHECK (rating_percentage >= 0 AND rating_percentage <= 100),
    dependent_status        VARCHAR(32) NOT NULL DEFAULT 'veteran_alone',
    monthly_amount_cents    INTEGER NOT NULL,
    cola_adjusted           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT va_rate_tables_unique UNIQUE (effective_date, rating_percentage, dependent_status)
);

COMMENT ON TABLE va_rate_tables IS 'VA disability compensation monthly rates by rating and dependent status';

-- cola_tables: Cost-of-Living Adjustment percentages
CREATE TABLE IF NOT EXISTS cola_tables (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    effective_date      DATE NOT NULL,
    cola_percentage     NUMERIC(6, 3) NOT NULL,
    fiscal_year         INTEGER,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT cola_tables_effective_unique UNIQUE (effective_date)
);

COMMENT ON TABLE cola_tables IS 'Annual COLA adjustment percentages applied to VA benefits';

-- alabama_ranking_metrics: Alabama veteran-friendliness benchmark data
CREATE TABLE IF NOT EXISTS alabama_ranking_metrics (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_key          VARCHAR(64) NOT NULL,
    metric_name         VARCHAR(255) NOT NULL,
    metric_value        NUMERIC(12, 4),
    metric_unit         VARCHAR(32),
    rank_national       INTEGER,
    rank_southeast      INTEGER,
    data_year           INTEGER NOT NULL,
    source              VARCHAR(255),
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT alabama_ranking_metrics_key_year_unique UNIQUE (metric_key, data_year)
);

COMMENT ON TABLE alabama_ranking_metrics IS 'Alabama-specific veteran quality-of-life and benefits ranking metrics';

CREATE TRIGGER trg_alabama_ranking_metrics_updated_at
    BEFORE UPDATE ON alabama_ranking_metrics
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- saved_state_comparisons: user-saved multi-state benefit comparisons
CREATE TABLE IF NOT EXISTS saved_state_comparisons (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    jurisdiction_ids    UUID[] NOT NULL DEFAULT '{}',
    comparison_data     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE saved_state_comparisons IS 'User-saved state benefit comparison snapshots';

CREATE TRIGGER trg_saved_state_comparisons_updated_at
    BEFORE UPDATE ON saved_state_comparisons
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- FACILITIES & RESOURCE OFFICERS
-- =============================================================================

-- facilities: VA medical centers, clinics, cemeteries
CREATE TABLE IF NOT EXISTS facilities (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    va_facility_id      VARCHAR(32),
    name                VARCHAR(512) NOT NULL,
    facility_type       VARCHAR(64) NOT NULL,
    address_line1       VARCHAR(255),
    city                VARCHAR(100),
    state_code          CHAR(2),
    postal_code         VARCHAR(20),
    latitude            NUMERIC(10, 7),
    longitude           NUMERIC(10, 7),
    phone               VARCHAR(32),
    website_url         TEXT,
    hours_of_operation  JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE facilities IS 'VA facilities directory (hospitals, clinics, regional offices)';

CREATE TRIGGER trg_facilities_updated_at
    BEFORE UPDATE ON facilities
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- resource_officer_assignments: VSO/RO to veteran caseload mapping
CREATE TABLE IF NOT EXISTS resource_officer_assignments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    officer_user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    veteran_user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id     UUID REFERENCES organizations(id) ON DELETE SET NULL,
    assigned_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at            TIMESTAMPTZ,
    is_primary          BOOLEAN NOT NULL DEFAULT TRUE,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ro_assignments_unique UNIQUE (officer_user_id, veteran_user_id, organization_id)
);

COMMENT ON TABLE resource_officer_assignments IS 'Maps resource officers to veterans they assist';

CREATE TRIGGER trg_ro_assignments_updated_at
    BEFORE UPDATE ON resource_officer_assignments
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- AUDIT, INTEGRATIONS, BILLING
-- =============================================================================

-- audit_logs: immutable admin action audit trail
CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id   UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(128) NOT NULL,
    resource_type   VARCHAR(64) NOT NULL,
    resource_id     UUID,
    old_values      JSONB,
    new_values      JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE audit_logs IS 'Immutable audit trail for admin and sensitive operations';

-- api_integration_logs: outbound API call telemetry (VA Lighthouse, Stripe, etc.)
CREATE TABLE IF NOT EXISTS api_integration_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_name      VARCHAR(64) NOT NULL,
    request_id          VARCHAR(64),
    endpoint            VARCHAR(512),
    http_method         VARCHAR(16),
    status_code         INTEGER,
    request_body        JSONB,
    response_body       JSONB,
    duration_ms         INTEGER,
    error_message       TEXT,
    user_id             UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE api_integration_logs IS 'Telemetry for external API integrations; PII redacted at app layer';

-- subscriptions: Stripe subscription state
CREATE TABLE IF NOT EXISTS subscriptions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id  VARCHAR(255) NOT NULL,
    stripe_customer_id      VARCHAR(255) NOT NULL,
    status                  VARCHAR(64) NOT NULL DEFAULT 'inactive',
    price_id                VARCHAR(255),
    amount_cents            INTEGER NOT NULL DEFAULT 599,
    currency                CHAR(3) NOT NULL DEFAULT 'USD',
    current_period_start    TIMESTAMPTZ,
    current_period_end      TIMESTAMPTZ,
    cancel_at_period_end    BOOLEAN NOT NULL DEFAULT FALSE,
    canceled_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT subscriptions_stripe_id_unique UNIQUE (stripe_subscription_id)
);

COMMENT ON TABLE subscriptions IS 'Consumer subscription records synced from Stripe webhooks ($5.99/month)';
COMMENT ON COLUMN subscriptions.amount_cents IS 'Default consumer tier: 599 cents ($5.99/month)';

CREATE TRIGGER trg_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- payment_events: Stripe webhook event log
CREATE TABLE IF NOT EXISTS payment_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID REFERENCES users(id) ON DELETE SET NULL,
    subscription_id     UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
    stripe_event_id     VARCHAR(255) NOT NULL,
    event_type          VARCHAR(128) NOT NULL,
    payload             JSONB NOT NULL DEFAULT '{}'::jsonb,
    processed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT payment_events_stripe_id_unique UNIQUE (stripe_event_id)
);

COMMENT ON TABLE payment_events IS 'Raw Stripe webhook events for idempotent payment processing';

-- =============================================================================
-- COMPLIANCE CHECKLISTS & OPERATIONS
-- =============================================================================

-- security_checklist: security hardening tracking for go-live
CREATE TABLE IF NOT EXISTS security_checklist (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_key        VARCHAR(128) NOT NULL,
    category        VARCHAR(64) NOT NULL,
    title           VARCHAR(512) NOT NULL,
    description     TEXT,
    status          VARCHAR(32) NOT NULL DEFAULT 'pending',
    priority        VARCHAR(16) NOT NULL DEFAULT 'medium',
    evidence_url    TEXT,
    completed_at    TIMESTAMPTZ,
    completed_by    UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT security_checklist_key_unique UNIQUE (item_key)
);

COMMENT ON TABLE security_checklist IS 'Security readiness checklist items (OWASP, encryption, RLS, etc.)';
COMMENT ON COLUMN security_checklist.status IS 'pending, in_progress, complete, not_applicable';

CREATE TRIGGER trg_security_checklist_updated_at
    BEFORE UPDATE ON security_checklist
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- legal_readiness_checklist: contracting and legal compliance tracking
CREATE TABLE IF NOT EXISTS legal_readiness_checklist (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_key        VARCHAR(128) NOT NULL,
    category        VARCHAR(64) NOT NULL,
    title           VARCHAR(512) NOT NULL,
    description     TEXT,
    status          VARCHAR(32) NOT NULL DEFAULT 'pending',
    priority        VARCHAR(16) NOT NULL DEFAULT 'medium',
    evidence_url    TEXT,
    completed_at    TIMESTAMPTZ,
    completed_by    UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT legal_readiness_key_unique UNIQUE (item_key)
);

COMMENT ON TABLE legal_readiness_checklist IS 'Legal and government contracting readiness (SDVOSB, SAM.gov, UEI, CAGE)';

CREATE TRIGGER trg_legal_readiness_updated_at
    BEFORE UPDATE ON legal_readiness_checklist
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- load_test_results: Locust / k6 performance test outcomes
CREATE TABLE IF NOT EXISTS load_test_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_run_id         VARCHAR(64) NOT NULL,
    scenario_name       VARCHAR(128) NOT NULL,
    concurrent_users    INTEGER NOT NULL,
    total_requests      INTEGER NOT NULL,
    success_rate        NUMERIC(5, 2),
    p50_ms              INTEGER,
    p95_ms              INTEGER,
    p99_ms              INTEGER,
    error_summary       JSONB NOT NULL DEFAULT '{}'::jsonb,
    environment         VARCHAR(64) NOT NULL DEFAULT 'staging',
    run_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE load_test_results IS 'Performance test results from Locust or k6 load testing runs';

-- notifications: in-app user notifications
CREATE TABLE IF NOT EXISTS notifications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               VARCHAR(255) NOT NULL,
    body                TEXT,
    notification_type   VARCHAR(64) NOT NULL DEFAULT 'info',
    is_read             BOOLEAN NOT NULL DEFAULT FALSE,
    read_at             TIMESTAMPTZ,
    action_url          TEXT,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE notifications IS 'In-app notifications for claim updates, payments, and system messages';
