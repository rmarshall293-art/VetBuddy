-- =============================================================================
-- VetBuddy Seed Data
-- =============================================================================
-- Demo / development seed data only. NO real PII.
-- Password for demo accounts: DemoPass123!
-- bcrypt hash (cost 12): $2b$12$SfAAhnZ5W055w1BHtkX8peZCydF.5DNK249bqF8ihZ3o6kDhfZwgy
-- Regenerate with: python -c "import bcrypt; print(bcrypt.hashpw(b'DemoPass123!', bcrypt.gensalt(12)).decode())"
-- =============================================================================

BEGIN;

-- Fixed UUIDs for deterministic references across environments
-- Demo users
--   veteran:      a0000000-0000-4000-8000-000000000001
--   admin:        a0000000-0000-4000-8000-000000000002
--   resource_off: a0000000-0000-4000-8000-000000000003
-- Demo org:       b0000000-0000-4000-8000-000000000001

-- -----------------------------------------------------------------------------
-- Roles
-- -----------------------------------------------------------------------------
INSERT INTO roles (id, name, description) VALUES
    ('c0000000-0000-4000-8000-000000000001', 'veteran', 'Veteran user with access to own claims and benefits'),
    ('c0000000-0000-4000-8000-000000000002', 'family_member', 'Family member with delegated veteran access'),
    ('c0000000-0000-4000-8000-000000000003', 'vso_resource_officer', 'VSO resource officer assisting assigned veterans'),
    ('c0000000-0000-4000-8000-000000000004', 'american_legion_resource_officer', 'American Legion resource officer'),
    ('c0000000-0000-4000-8000-000000000005', 'department_admin', 'Department-level administrator'),
    ('c0000000-0000-4000-8000-000000000006', 'super_admin', 'Platform super administrator')
ON CONFLICT (name) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Organizations
-- -----------------------------------------------------------------------------
INSERT INTO organizations (id, name, org_type, state_code, contact_email, uei, cage_code) VALUES
    ('b0000000-0000-4000-8000-000000000001', 'Demo Alabama VSO Chapter', 'vso', 'AL', 'demo.vso@vetbuddy.local', 'DEMOUEI00001', 'DEMO1'),
    ('b0000000-0000-4000-8000-000000000002', 'Demo American Legion Post 100', 'american_legion', 'AL', 'demo.legion@vetbuddy.local', 'DEMOUEI00002', 'DEMO2')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Demo Users
-- -----------------------------------------------------------------------------
INSERT INTO users (id, email, password_hash, is_active, email_verified, mfa_enabled) VALUES
    (
        'a0000000-0000-4000-8000-000000000001',
        'demo.veteran@vetbuddy.local',
        '$2b$12$SfAAhnZ5W055w1BHtkX8peZCydF.5DNK249bqF8ihZ3o6kDhfZwgy',
        TRUE, TRUE, FALSE
    ),
    (
        'a0000000-0000-4000-8000-000000000002',
        'demo.admin@vetbuddy.local',
        '$2b$12$SfAAhnZ5W055w1BHtkX8peZCydF.5DNK249bqF8ihZ3o6kDhfZwgy',
        TRUE, TRUE, FALSE
    ),
    (
        'a0000000-0000-4000-8000-000000000003',
        'demo.officer@vetbuddy.local',
        '$2b$12$SfAAhnZ5W055w1BHtkX8peZCydF.5DNK249bqF8ihZ3o6kDhfZwgy',
        TRUE, TRUE, FALSE
    )
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_roles (user_id, role_id) VALUES
    ('a0000000-0000-4000-8000-000000000001', 'c0000000-0000-4000-8000-000000000001'),
    ('a0000000-0000-4000-8000-000000000002', 'c0000000-0000-4000-8000-000000000006'),
    ('a0000000-0000-4000-8000-000000000003', 'c0000000-0000-4000-8000-000000000003')
ON CONFLICT (user_id, role_id, organization_id) DO NOTHING;

INSERT INTO user_profiles (user_id, first_name, last_name, state_code, branch_of_service, service_start_date, service_end_date) VALUES
    ('a0000000-0000-4000-8000-000000000001', 'Demo', 'Veteran', 'AL', 'Army', '2008-06-01', '2016-08-15'),
    ('a0000000-0000-4000-8000-000000000002', 'Demo', 'Admin', 'AL', NULL, NULL, NULL),
    ('a0000000-0000-4000-8000-000000000003', 'Demo', 'Officer', 'AL', NULL, NULL, NULL)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO resource_officer_assignments (officer_user_id, veteran_user_id, organization_id, is_primary) VALUES
    (
        'a0000000-0000-4000-8000-000000000003',
        'a0000000-0000-4000-8000-000000000001',
        'b0000000-0000-4000-8000-000000000001',
        TRUE
    )
ON CONFLICT (officer_user_id, veteran_user_id, organization_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Jurisdictions (AL, TX, FL minimum)
-- -----------------------------------------------------------------------------
INSERT INTO jurisdictions (id, name, abbreviation, fips_code, is_state, veteran_population_estimate) VALUES
    ('d0000000-0000-4000-8000-000000000001', 'Alabama', 'AL', '01', TRUE, 380000),
    ('d0000000-0000-4000-8000-000000000002', 'Texas', 'TX', '48', TRUE, 1650000),
    ('d0000000-0000-4000-8000-000000000003', 'Florida', 'FL', '12', TRUE, 1480000)
ON CONFLICT (abbreviation) DO NOTHING;

-- Update veteran preferred jurisdiction
UPDATE user_profiles
SET preferred_jurisdiction_id = 'd0000000-0000-4000-8000-000000000001'
WHERE user_id = 'a0000000-0000-4000-8000-000000000001';

-- -----------------------------------------------------------------------------
-- Benefits
-- -----------------------------------------------------------------------------
INSERT INTO benefits (id, code, name, description, category, is_federal, source_url) VALUES
    ('e0000000-0000-4000-8000-000000000001', 'va_disability_comp', 'VA Disability Compensation', 'Monthly tax-free compensation for service-connected disabilities', 'compensation', TRUE, 'https://www.va.gov/disability/'),
    ('e0000000-0000-4000-8000-000000000002', 'va_healthcare', 'VA Health Care', 'Medical care through VA facilities and community providers', 'healthcare', TRUE, 'https://www.va.gov/health-care/'),
    ('e0000000-0000-4000-8000-000000000003', 'gi_bill', 'GI Bill Education Benefits', 'Education and training benefits for veterans and dependents', 'education', TRUE, 'https://www.va.gov/education/'),
    ('e0000000-0000-4000-8000-000000000004', 'al_property_tax_exempt', 'Alabama Disabled Veteran Property Tax Exemption', 'Full property tax exemption for 100% disabled veterans', 'tax', FALSE, 'https://www.revenue.alabama.gov/'),
    ('e0000000-0000-4000-8000-000000000005', 'tx_hazlewood', 'Texas Hazlewood Act', 'Tuition exemption at Texas public institutions for veterans', 'education', FALSE, 'https://www.tvc.texas.gov/'),
    ('e0000000-0000-4000-8000-000000000006', 'fl_property_tax_discount', 'Florida Veteran Property Tax Discount', 'Property tax discount for disabled veterans by rating percentage', 'tax', FALSE, 'https://floridarevenue.com/')
ON CONFLICT (code) DO NOTHING;

-- Jurisdiction benefits mapping
INSERT INTO jurisdiction_benefits (jurisdiction_id, benefit_id, is_available, eligibility_notes, amount_min_cents, amount_max_cents, effective_date) VALUES
    ('d0000000-0000-4000-8000-000000000001', 'e0000000-0000-4000-8000-000000000004', TRUE, '100% permanent and total disability rating required', 0, NULL, '2024-01-01'),
    ('d0000000-0000-4000-8000-000000000002', 'e0000000-0000-4000-8000-000000000005', TRUE, 'Texas resident; 181 days active duty', 0, NULL, '2024-01-01'),
    ('d0000000-0000-4000-8000-000000000003', 'e0000000-0000-4000-8000-000000000006', TRUE, 'Rating-based discount: 10%-100%', 0, NULL, '2024-01-01')
ON CONFLICT (jurisdiction_id, benefit_id, effective_date) DO NOTHING;

-- State tax rules
INSERT INTO state_tax_rules (jurisdiction_id, tax_year, military_retirement_exempt, va_disability_exempt, partial_exemption_notes) VALUES
    ('d0000000-0000-4000-8000-000000000001', 2025, FALSE, TRUE, 'Military retirement partially exempt up to $6,000 for age 65+'),
    ('d0000000-0000-4000-8000-000000000002', 2025, FALSE, TRUE, 'No state income tax'),
    ('d0000000-0000-4000-8000-000000000003', 2025, TRUE, TRUE, 'Military retirement exempt for veterans with 25+ years service')
ON CONFLICT (jurisdiction_id, tax_year) DO NOTHING;

-- VA rate table sample (2025 effective, veteran alone)
INSERT INTO va_rate_tables (effective_date, rating_percentage, dependent_status, monthly_amount_cents) VALUES
    ('2025-01-01', 10, 'veteran_alone', 17123),
    ('2025-01-01', 30, 'veteran_alone', 52431),
    ('2025-01-01', 50, 'veteran_alone', 107541),
    ('2025-01-01', 70, 'veteran_alone', 171231),
    ('2025-01-01', 100, 'veteran_alone', 373738)
ON CONFLICT (effective_date, rating_percentage, dependent_status) DO NOTHING;

-- COLA table
INSERT INTO cola_tables (effective_date, cola_percentage, fiscal_year, notes) VALUES
    ('2025-01-01', 2.500, 2025, '2025 COLA adjustment per VA announcement (demo value)')
ON CONFLICT (effective_date) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Alabama ranking metrics
-- -----------------------------------------------------------------------------
INSERT INTO alabama_ranking_metrics (metric_key, metric_name, metric_value, metric_unit, rank_national, rank_southeast, data_year, source, notes) VALUES
    ('veteran_population_pct', 'Veteran Population Percentage', 8.2, 'percent', 12, 3, 2025, 'VA VetPop2023 (demo)', 'Percentage of state population who are veterans'),
    ('state_benefit_score', 'State Veteran Benefits Score', 72.5, 'score', 28, 6, 2025, 'VetBuddy internal benchmark (demo)', 'Composite score of state-level veteran benefits'),
    ('va_facility_access', 'VA Facility Access Index', 65.0, 'index', 35, 8, 2025, 'VA Facility Locator (demo)', 'Proximity and capacity index for VA facilities'),
    ('employment_rate', 'Veteran Employment Rate', 94.2, 'percent', 18, 4, 2025, 'BLS demo data', 'Veteran civilian employment rate'),
    ('homelessness_rate', 'Veteran Homelessness Rate', 0.18, 'percent', 22, 5, 2025, 'HUD PIT demo data', 'Point-in-time veteran homelessness rate')
ON CONFLICT (metric_key, data_year) DO NOTHING;

-- -----------------------------------------------------------------------------
-- VA Forms catalog
-- -----------------------------------------------------------------------------
INSERT INTO va_forms (form_number, title, description, version, category, is_active) VALUES
    ('21-526EZ', 'Application for Disability Compensation and Related Compensation Benefits', 'Primary disability compensation application', '2024-06', 'compensation', TRUE),
    ('21-4138', 'Statement in Support of Claim', 'Sworn statement to support a claim', '2023-07', 'supporting', TRUE),
    ('21-0966', 'Intent to File a Claim for Compensation and/or Pension', 'Preserves effective date for up to one year', '2023-08', 'intent_to_file', TRUE),
    ('21-4142', 'Authorization to Disclose Information to VA', 'Authorizes release of private medical records', '2022-05', 'medical', TRUE),
    ('10-10EZ', 'Application for Health Benefits', 'Enrollment in VA health care', '2024-01', 'healthcare', TRUE),
    ('22-1990', 'Application for VA Education Benefits', 'Apply for GI Bill and related education benefits', '2023-12', 'education', TRUE),
    ('26-1880', 'Request for a Certificate of Eligibility', 'Home loan COE request', '2023-03', 'housing', TRUE)
ON CONFLICT (form_number, version) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Security checklist items
-- -----------------------------------------------------------------------------
INSERT INTO security_checklist (item_key, category, title, description, status, priority) VALUES
    ('sec_jwt_rotation', 'authentication', 'JWT Secret Rotation Policy', 'Document and implement quarterly JWT secret rotation in production', 'pending', 'high'),
    ('sec_mfa_enforcement', 'authentication', 'MFA for Admin Accounts', 'Require MFA for department_admin and super_admin roles', 'pending', 'high'),
    ('sec_password_policy', 'authentication', 'Password Complexity Policy', 'Enforce NIST 800-63B aligned password requirements', 'in_progress', 'medium'),
    ('sec_rls_enabled', 'database', 'Row-Level Security Enabled', 'Verify RLS policies active on all sensitive tables', 'complete', 'high'),
    ('sec_encryption_at_rest', 'encryption', 'Encryption at Rest', 'Confirm Postgres and object storage encryption enabled', 'pending', 'high'),
    ('sec_tls_enforced', 'transport', 'TLS 1.2+ Enforced', 'HTTPS only; HSTS enabled on all endpoints', 'pending', 'high'),
    ('sec_secrets_manager', 'secrets', 'Secrets in Environment/Manager', 'No secrets in source control; use vault or cloud secrets manager', 'in_progress', 'high'),
    ('sec_rate_limiting', 'api', 'API Rate Limiting', 'Rate limit auth and sensitive endpoints', 'pending', 'medium'),
    ('sec_audit_logging', 'monitoring', 'Audit Logging', 'Immutable audit trail for admin actions', 'complete', 'high'),
    ('sec_dependency_scan', 'supply_chain', 'Dependency Vulnerability Scanning', 'CI pipeline runs pip/npm audit on every PR', 'pending', 'medium'),
    ('sec_pii_redaction', 'data', 'PII Redaction in Logs', 'Redact SSN, VA file numbers, and medical data from application logs', 'pending', 'high'),
    ('sec_cors_lockdown', 'api', 'CORS Origin Lockdown', 'Restrict CORS to known frontend origins in production', 'pending', 'medium')
ON CONFLICT (item_key) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Legal readiness checklist items
-- -----------------------------------------------------------------------------
INSERT INTO legal_readiness_checklist (item_key, category, title, description, status, priority) VALUES
    ('legal_sdvosb_cert', 'certification', 'SDVOSB Certification', 'Obtain Service-Disabled Veteran-Owned Small Business certification via SBA VetCert', 'pending', 'high'),
    ('legal_sam_registration', 'registration', 'SAM.gov Registration', 'Register entity in System for Award Management (SAM.gov)', 'pending', 'high'),
    ('legal_uei_obtained', 'registration', 'UEI Obtained', 'Obtain Unique Entity Identifier from SAM.gov', 'pending', 'high'),
    ('legal_cage_code', 'registration', 'CAGE Code Assigned', 'Obtain CAGE code via SAM.gov registration', 'pending', 'high'),
    ('legal_privacy_policy', 'compliance', 'Privacy Policy Published', 'Publish privacy policy covering veteran PII and HIPAA-adjacent data', 'pending', 'high'),
    ('legal_terms_of_service', 'compliance', 'Terms of Service', 'Publish terms of service for consumer subscription tier', 'pending', 'medium'),
    ('legal_data_processing', 'compliance', 'Data Processing Agreement', 'DPA templates for B2B VSO partnerships', 'pending', 'medium'),
    ('legal_va_disclaimer', 'compliance', 'VA Non-Affiliation Disclaimer', 'Display clear disclaimer that VetBuddy is not affiliated with VA', 'complete', 'high'),
    ('legal_stripe_tos', 'payments', 'Stripe Terms Compliance', 'Ensure Stripe Connect/Checkout compliance for subscription billing', 'pending', 'medium'),
    ('legal_accessibility', 'compliance', 'Section 508 / WCAG 2.1 AA', 'Accessibility audit and remediation plan', 'pending', 'medium'),
    ('legal_insurance', 'risk', 'Cyber Liability Insurance', 'Obtain cyber liability and E&O insurance coverage', 'pending', 'high'),
    ('legal_incident_response', 'security', 'Incident Response Plan', 'Document breach notification and incident response procedures', 'pending', 'high')
ON CONFLICT (item_key) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Demo claim for veteran user
-- -----------------------------------------------------------------------------
INSERT INTO claims (id, user_id, claim_type, status, filing_date, combined_rating, notes) VALUES
    (
        'f0000000-0000-4000-8000-000000000001',
        'a0000000-0000-4000-8000-000000000001',
        'initial',
        'pending',
        '2025-03-15',
        NULL,
        'Demo claim for development and testing'
    )
ON CONFLICT (id) DO NOTHING;

INSERT INTO claim_conditions (claim_id, condition_name, diagnostic_code, claimed_rating, status) VALUES
    ('f0000000-0000-4000-8000-000000000001', 'Tinnitus', '6260', 10, 'pending'),
    ('f0000000-0000-4000-8000-000000000001', 'Post-Traumatic Stress Disorder', '9411', 50, 'pending');

-- Demo notification
INSERT INTO notifications (user_id, title, body, notification_type) VALUES
    (
        'a0000000-0000-4000-8000-000000000001',
        'Welcome to VetBuddy',
        'Your demo account is ready. This is a development environment with mock VA integration.',
        'info'
    );

COMMIT;
