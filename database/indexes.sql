-- =============================================================================
-- VetBuddy Database Indexes
-- =============================================================================
-- Performance indexes for common query patterns.
-- Run after schema.sql. Safe to re-run (IF NOT EXISTS).
-- =============================================================================

-- Users -----------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id
    ON users (stripe_customer_id)
    WHERE stripe_customer_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_oauth
    ON users (oauth_provider, oauth_subject)
    WHERE oauth_provider IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_deleted_at
    ON users (deleted_at)
    WHERE deleted_at IS NOT NULL;

-- User profiles ---------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id
    ON user_profiles (user_id);

CREATE INDEX IF NOT EXISTS idx_user_profiles_state_code
    ON user_profiles (state_code);

-- Roles -----------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id
    ON user_roles (user_id);

CREATE INDEX IF NOT EXISTS idx_user_roles_role_id
    ON user_roles (role_id);

CREATE INDEX IF NOT EXISTS idx_user_roles_org_id
    ON user_roles (organization_id)
    WHERE organization_id IS NOT NULL;

-- Sessions --------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_sessions_jti
    ON sessions (jti);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id
    ON sessions (user_id);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
    ON sessions (expires_at)
    WHERE revoked_at IS NULL;

-- Claims ----------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_claims_user_id
    ON claims (user_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_claims_status
    ON claims (status)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_claims_va_claim_id
    ON claims (va_claim_id)
    WHERE va_claim_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_claims_filing_date
    ON claims (filing_date DESC)
    WHERE deleted_at IS NULL;

-- Claim conditions & evidence -------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_claim_conditions_claim_id
    ON claim_conditions (claim_id);

CREATE INDEX IF NOT EXISTS idx_claim_evidence_claim_id
    ON claim_evidence (claim_id);

CREATE INDEX IF NOT EXISTS idx_claim_evidence_document_id
    ON claim_evidence (document_id)
    WHERE document_id IS NOT NULL;

-- Documents -------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_documents_user_id
    ON documents (user_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_documents_claim_id
    ON documents (claim_id)
    WHERE claim_id IS NOT NULL AND deleted_at IS NULL;

-- Intent to file --------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_itf_user_id
    ON intent_to_file_records (user_id);

CREATE INDEX IF NOT EXISTS idx_itf_status
    ON intent_to_file_records (status);

-- Jurisdictions ---------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_jurisdictions_abbreviation
    ON jurisdictions (abbreviation);

-- Jurisdiction benefits -------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_jurisdiction_benefits_jurisdiction_id
    ON jurisdiction_benefits (jurisdiction_id);

CREATE INDEX IF NOT EXISTS idx_jurisdiction_benefits_benefit_id
    ON jurisdiction_benefits (benefit_id);

-- State tax rules -------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_state_tax_rules_jurisdiction_year
    ON state_tax_rules (jurisdiction_id, tax_year);

-- VA rate tables --------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_va_rate_tables_effective
    ON va_rate_tables (effective_date DESC, rating_percentage);

-- Facilities ------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_facilities_state_code
    ON facilities (state_code);

CREATE INDEX IF NOT EXISTS idx_facilities_type
    ON facilities (facility_type);

-- Resource officer assignments ------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_ro_assignments_officer
    ON resource_officer_assignments (officer_user_id)
    WHERE ended_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_ro_assignments_veteran
    ON resource_officer_assignments (veteran_user_id)
    WHERE ended_at IS NULL;

-- Organizations ---------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_organizations_org_type
    ON organizations (org_type)
    WHERE deleted_at IS NULL;

-- Audit logs ------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor
    ON audit_logs (actor_user_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_resource
    ON audit_logs (resource_type, resource_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
    ON audit_logs (created_at DESC);

-- API integration logs --------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_api_logs_integration
    ON api_integration_logs (integration_name, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_api_logs_user_id
    ON api_integration_logs (user_id)
    WHERE user_id IS NOT NULL;

-- Subscriptions & payments ----------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id
    ON subscriptions (user_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer
    ON subscriptions (stripe_customer_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_status
    ON subscriptions (status);

CREATE INDEX IF NOT EXISTS idx_payment_events_user_id
    ON payment_events (user_id);

CREATE INDEX IF NOT EXISTS idx_payment_events_subscription_id
    ON payment_events (subscription_id);

CREATE INDEX IF NOT EXISTS idx_payment_events_type
    ON payment_events (event_type, created_at DESC);

-- Notifications ---------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_notifications_user_id
    ON notifications (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_unread
    ON notifications (user_id)
    WHERE is_read = FALSE;

-- Saved comparisons -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_saved_comparisons_user_id
    ON saved_state_comparisons (user_id);

-- Alabama ranking metrics -----------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_alabama_metrics_year
    ON alabama_ranking_metrics (data_year DESC);

CREATE INDEX IF NOT EXISTS idx_alabama_metrics_key
    ON alabama_ranking_metrics (metric_key);

-- Checklists ------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_security_checklist_status
    ON security_checklist (status, priority);

CREATE INDEX IF NOT EXISTS idx_legal_readiness_status
    ON legal_readiness_checklist (status, priority);

-- Load test results -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_load_test_run_at
    ON load_test_results (run_at DESC);

CREATE INDEX IF NOT EXISTS idx_load_test_scenario
    ON load_test_results (scenario_name, environment);
