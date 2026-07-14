-- =============================================================================
-- VetBuddy Row-Level Security (RLS) Policies
-- =============================================================================
--
-- APP-LEVEL AUTHORIZATION NOTE:
-- VetBuddy's FastAPI backend enforces authorization via JWT validation and
-- role-based access control (RBAC) in application code. These RLS policies
-- provide defense-in-depth when clients connect directly to Postgres (e.g.,
-- Supabase PostgREST, Supabase Realtime, or ad-hoc SQL with a user JWT).
--
-- In production, prefer routing all data access through the FastAPI API layer.
-- When using Supabase client libraries, ensure the JWT carries role claims
-- matching the helper functions below.
--
-- Policy summary:
--   1. Users read/update own profile
--   2. Veterans own claims only
--   3. Resource officers see assigned veterans
--   4. Department admins see org-level records
--   5. Super admins see all admin records
--   6. Payment records: owner + admins
--   7. Audit logs: admin-only
--   8. Legal/security checklist: admin-only
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Helper functions for JWT claim extraction (Supabase-compatible)
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION auth_user_id()
RETURNS UUID AS $$
BEGIN
    -- Supabase sets request.jwt.claim.sub; fall back to app custom claim
    RETURN COALESCE(
        NULLIF(current_setting('request.jwt.claim.sub', TRUE), '')::UUID,
        NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID
    );
EXCEPTION
    WHEN OTHERS THEN RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION auth_user_id() IS
    'Extract authenticated user UUID from JWT sub claim or app.current_user_id setting';

CREATE OR REPLACE FUNCTION auth_user_roles()
RETURNS TEXT[] AS $$
DECLARE
    roles_json TEXT;
BEGIN
    roles_json := current_setting('request.jwt.claim.roles', TRUE);
    IF roles_json IS NULL OR roles_json = '' THEN
        RETURN ARRAY[]::TEXT[];
    END IF;
    RETURN ARRAY(SELECT jsonb_array_elements_text(roles_json::jsonb));
EXCEPTION
    WHEN OTHERS THEN RETURN ARRAY[]::TEXT[];
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION has_role(role_name TEXT)
RETURNS BOOLEAN AS $$
    SELECT role_name = ANY(auth_user_roles());
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION is_super_admin()
RETURNS BOOLEAN AS $$
    SELECT has_role('super_admin');
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION is_department_admin()
RETURNS BOOLEAN AS $$
    SELECT has_role('department_admin') OR is_super_admin();
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION is_resource_officer()
RETURNS BOOLEAN AS $$
    SELECT has_role('vso_resource_officer')
        OR has_role('american_legion_resource_officer')
        OR is_department_admin();
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
    SELECT is_department_admin();
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION is_assigned_veteran(veteran_id UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1
        FROM resource_officer_assignments roa
        WHERE roa.officer_user_id = auth_user_id()
          AND roa.veteran_user_id = veteran_id
          AND roa.ended_at IS NULL
    );
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- Enable RLS on protected tables
-- -----------------------------------------------------------------------------

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE claim_conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE claim_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE intent_to_file_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE resource_officer_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_checklist ENABLE ROW LEVEL SECURITY;
ALTER TABLE legal_readiness_checklist ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_state_comparisons ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_integration_logs ENABLE ROW LEVEL SECURITY;

-- Reference tables: read-only for authenticated users
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE benefits ENABLE ROW LEVEL SECURITY;
ALTER TABLE jurisdictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE jurisdiction_benefits ENABLE ROW LEVEL SECURITY;
ALTER TABLE state_tax_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE va_rate_tables ENABLE ROW LEVEL SECURITY;
ALTER TABLE cola_tables ENABLE ROW LEVEL SECURITY;
ALTER TABLE va_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE facilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE alabama_ranking_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE load_test_results ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- 1. Users: read/update own profile
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS users_select_own ON users;
CREATE POLICY users_select_own ON users
    FOR SELECT
    USING (
        id = auth_user_id()
        OR is_admin()
        OR (is_resource_officer() AND is_assigned_veteran(id))
    );

DROP POLICY IF EXISTS users_update_own ON users;
CREATE POLICY users_update_own ON users
    FOR UPDATE
    USING (id = auth_user_id() OR is_super_admin())
    WITH CHECK (id = auth_user_id() OR is_super_admin());

-- -----------------------------------------------------------------------------
-- user_profiles: read/update own
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS profiles_select ON user_profiles;
CREATE POLICY profiles_select ON user_profiles
    FOR SELECT
    USING (
        user_id = auth_user_id()
        OR is_admin()
        OR (is_resource_officer() AND is_assigned_veteran(user_id))
    );

DROP POLICY IF EXISTS profiles_update_own ON user_profiles;
CREATE POLICY profiles_update_own ON user_profiles
    FOR UPDATE
    USING (user_id = auth_user_id() OR is_admin())
    WITH CHECK (user_id = auth_user_id() OR is_admin());

DROP POLICY IF EXISTS profiles_insert_own ON user_profiles;
CREATE POLICY profiles_insert_own ON user_profiles
    FOR INSERT
    WITH CHECK (user_id = auth_user_id() OR is_super_admin());

-- -----------------------------------------------------------------------------
-- user_roles: users see own roles; admins see all
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS user_roles_select ON user_roles;
CREATE POLICY user_roles_select ON user_roles
    FOR SELECT
    USING (user_id = auth_user_id() OR is_admin());

-- -----------------------------------------------------------------------------
-- sessions: own sessions only
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS sessions_own ON sessions;
CREATE POLICY sessions_own ON sessions
    FOR ALL
    USING (user_id = auth_user_id() OR is_super_admin())
    WITH CHECK (user_id = auth_user_id() OR is_super_admin());

-- -----------------------------------------------------------------------------
-- 2. Claims: veterans own claims only (+ RO/admin overrides)
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS claims_select ON claims;
CREATE POLICY claims_select ON claims
    FOR SELECT
    USING (
        (user_id = auth_user_id() AND deleted_at IS NULL)
        OR (is_resource_officer() AND is_assigned_veteran(user_id) AND deleted_at IS NULL)
        OR is_admin()
    );

DROP POLICY IF EXISTS claims_insert_own ON claims;
CREATE POLICY claims_insert_own ON claims
    FOR INSERT
    WITH CHECK (user_id = auth_user_id() OR is_admin());

DROP POLICY IF EXISTS claims_update ON claims;
CREATE POLICY claims_update ON claims
    FOR UPDATE
    USING (
        user_id = auth_user_id()
        OR (is_resource_officer() AND is_assigned_veteran(user_id))
        OR is_admin()
    )
    WITH CHECK (
        user_id = auth_user_id()
        OR (is_resource_officer() AND is_assigned_veteran(user_id))
        OR is_admin()
    );

-- claim_conditions & claim_evidence inherit claim ownership
DROP POLICY IF EXISTS claim_conditions_access ON claim_conditions;
CREATE POLICY claim_conditions_access ON claim_conditions
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM claims c
            WHERE c.id = claim_conditions.claim_id
              AND c.deleted_at IS NULL
              AND (
                  c.user_id = auth_user_id()
                  OR (is_resource_officer() AND is_assigned_veteran(c.user_id))
                  OR is_admin()
              )
        )
    );

DROP POLICY IF EXISTS claim_evidence_access ON claim_evidence;
CREATE POLICY claim_evidence_access ON claim_evidence
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM claims c
            WHERE c.id = claim_evidence.claim_id
              AND c.deleted_at IS NULL
              AND (
                  c.user_id = auth_user_id()
                  OR (is_resource_officer() AND is_assigned_veteran(c.user_id))
                  OR is_admin()
              )
        )
    );

-- -----------------------------------------------------------------------------
-- documents: owner + assigned RO + admin
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS documents_access ON documents;
CREATE POLICY documents_access ON documents
    FOR ALL
    USING (
        (user_id = auth_user_id() AND deleted_at IS NULL)
        OR (is_resource_officer() AND is_assigned_veteran(user_id) AND deleted_at IS NULL)
        OR is_admin()
    )
    WITH CHECK (
        user_id = auth_user_id()
        OR (is_resource_officer() AND is_assigned_veteran(user_id))
        OR is_admin()
    );

-- intent_to_file: veteran owns
DROP POLICY IF EXISTS itf_access ON intent_to_file_records;
CREATE POLICY itf_access ON intent_to_file_records
    FOR ALL
    USING (
        user_id = auth_user_id()
        OR (is_resource_officer() AND is_assigned_veteran(user_id))
        OR is_admin()
    )
    WITH CHECK (
        user_id = auth_user_id()
        OR is_admin()
    );

-- -----------------------------------------------------------------------------
-- 3. Resource officers: assigned veterans
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS ro_assignments_select ON resource_officer_assignments;
CREATE POLICY ro_assignments_select ON resource_officer_assignments
    FOR SELECT
    USING (
        officer_user_id = auth_user_id()
        OR veteran_user_id = auth_user_id()
        OR is_admin()
    );

DROP POLICY IF EXISTS ro_assignments_manage ON resource_officer_assignments;
CREATE POLICY ro_assignments_manage ON resource_officer_assignments
    FOR ALL
    USING (is_admin() OR officer_user_id = auth_user_id())
    WITH CHECK (is_admin() OR officer_user_id = auth_user_id());

-- -----------------------------------------------------------------------------
-- 4. Department admins: org-level access
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS organizations_admin ON organizations;
CREATE POLICY organizations_admin ON organizations
    FOR SELECT
    USING (TRUE);  -- public org directory

DROP POLICY IF EXISTS organizations_manage ON organizations;
CREATE POLICY organizations_manage ON organizations
    FOR ALL
    USING (is_department_admin())
    WITH CHECK (is_department_admin());

-- -----------------------------------------------------------------------------
-- 5. Super admins: full admin record access (via is_admin / is_super_admin)
--    Covered by individual policies above using is_admin() / is_super_admin().
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- 6. Payment records: owner + admins
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS subscriptions_owner ON subscriptions;
CREATE POLICY subscriptions_owner ON subscriptions
    FOR SELECT
    USING (user_id = auth_user_id() OR is_admin());

DROP POLICY IF EXISTS subscriptions_manage ON subscriptions;
CREATE POLICY subscriptions_manage ON subscriptions
    FOR ALL
    USING (is_super_admin())
    WITH CHECK (is_super_admin());

DROP POLICY IF EXISTS payment_events_owner ON payment_events;
CREATE POLICY payment_events_owner ON payment_events
    FOR SELECT
    USING (user_id = auth_user_id() OR is_admin());

DROP POLICY IF EXISTS payment_events_insert ON payment_events;
CREATE POLICY payment_events_insert ON payment_events
    FOR INSERT
    WITH CHECK (is_super_admin());  -- webhook handler uses service role

-- -----------------------------------------------------------------------------
-- 7. Audit logs: admin-only
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS audit_logs_admin ON audit_logs;
CREATE POLICY audit_logs_admin ON audit_logs
    FOR ALL
    USING (is_admin())
    WITH CHECK (is_admin());

DROP POLICY IF EXISTS api_logs_admin ON api_integration_logs;
CREATE POLICY api_logs_admin ON api_integration_logs
    FOR SELECT
    USING (is_admin() OR user_id = auth_user_id());

-- -----------------------------------------------------------------------------
-- 8. Legal/security checklist: admin-only
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS security_checklist_admin ON security_checklist;
CREATE POLICY security_checklist_admin ON security_checklist
    FOR ALL
    USING (is_admin())
    WITH CHECK (is_admin());

DROP POLICY IF EXISTS legal_checklist_admin ON legal_readiness_checklist;
CREATE POLICY legal_checklist_admin ON legal_readiness_checklist
    FOR ALL
    USING (is_admin())
    WITH CHECK (is_admin());

DROP POLICY IF EXISTS load_test_admin ON load_test_results;
CREATE POLICY load_test_admin ON load_test_results
    FOR ALL
    USING (is_admin())
    WITH CHECK (is_admin());

-- -----------------------------------------------------------------------------
-- Notifications & saved comparisons: owner only
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS notifications_own ON notifications;
CREATE POLICY notifications_own ON notifications
    FOR ALL
    USING (user_id = auth_user_id())
    WITH CHECK (user_id = auth_user_id());

DROP POLICY IF EXISTS saved_comparisons_own ON saved_state_comparisons;
CREATE POLICY saved_comparisons_own ON saved_state_comparisons
    FOR ALL
    USING (user_id = auth_user_id())
    WITH CHECK (user_id = auth_user_id());

-- -----------------------------------------------------------------------------
-- Public reference data: authenticated read
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS roles_read ON roles;
CREATE POLICY roles_read ON roles FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS benefits_read ON benefits;
CREATE POLICY benefits_read ON benefits FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS jurisdictions_read ON jurisdictions;
CREATE POLICY jurisdictions_read ON jurisdictions FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS jurisdiction_benefits_read ON jurisdiction_benefits;
CREATE POLICY jurisdiction_benefits_read ON jurisdiction_benefits FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS state_tax_read ON state_tax_rules;
CREATE POLICY state_tax_read ON state_tax_rules FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS va_rates_read ON va_rate_tables;
CREATE POLICY va_rates_read ON va_rate_tables FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS cola_read ON cola_tables;
CREATE POLICY cola_read ON cola_tables FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS va_forms_read ON va_forms;
CREATE POLICY va_forms_read ON va_forms FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS facilities_read ON facilities;
CREATE POLICY facilities_read ON facilities FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS alabama_metrics_read ON alabama_ranking_metrics;
CREATE POLICY alabama_metrics_read ON alabama_ranking_metrics FOR SELECT USING (TRUE);
