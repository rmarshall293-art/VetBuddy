-- =============================================================================
-- VetBuddy Database Views
-- =============================================================================
-- Read-optimized views for dashboards and reporting.
-- These views respect underlying table RLS when queried via Supabase client.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- claims_dashboard_view
-- Aggregated claim summary per veteran for the claims management dashboard.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW claims_dashboard_view AS
SELECT
    c.id                    AS claim_id,
    c.user_id,
    u.email                 AS user_email,
    up.first_name,
    up.last_name,
    c.claim_type,
    c.status                AS claim_status,
    c.va_claim_id,
    c.filing_date,
    c.decision_date,
    c.combined_rating,
    c.created_at            AS claim_created_at,
    c.updated_at            AS claim_updated_at,
    COUNT(DISTINCT cc.id)   AS condition_count,
    COUNT(DISTINCT ce.id)   AS evidence_count,
    COUNT(DISTINCT d.id)    AS document_count,
    COALESCE(
        json_agg(
            DISTINCT jsonb_build_object(
                'id', cc.id,
                'name', cc.condition_name,
                'status', cc.status,
                'claimed_rating', cc.claimed_rating,
                'granted_rating', cc.granted_rating
            )
        ) FILTER (WHERE cc.id IS NOT NULL),
        '[]'::json
    )                       AS conditions_summary
FROM claims c
JOIN users u ON u.id = c.user_id AND u.deleted_at IS NULL
LEFT JOIN user_profiles up ON up.user_id = c.user_id
LEFT JOIN claim_conditions cc ON cc.claim_id = c.id
LEFT JOIN claim_evidence ce ON ce.claim_id = c.id
LEFT JOIN documents d ON d.claim_id = c.id AND d.deleted_at IS NULL
WHERE c.deleted_at IS NULL
GROUP BY
    c.id, c.user_id, u.email, up.first_name, up.last_name,
    c.claim_type, c.status, c.va_claim_id, c.filing_date,
    c.decision_date, c.combined_rating, c.created_at, c.updated_at;

COMMENT ON VIEW claims_dashboard_view IS
    'Per-claim dashboard summary with condition, evidence, and document counts';

-- -----------------------------------------------------------------------------
-- user_benefits_dashboard_view
-- Personalized benefits view combining federal VA rates and state benefits
-- for the user''s preferred jurisdiction.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW user_benefits_dashboard_view AS
SELECT
    u.id                            AS user_id,
    u.email,
    up.first_name,
    up.last_name,
    up.state_code                   AS residence_state_code,
    j.id                            AS preferred_jurisdiction_id,
    j.name                          AS preferred_jurisdiction_name,
    j.abbreviation                  AS preferred_jurisdiction_abbr,
    b.id                            AS benefit_id,
    b.code                          AS benefit_code,
    b.name                          AS benefit_name,
    b.category                      AS benefit_category,
    b.is_federal,
    jb.is_available                 AS available_in_jurisdiction,
    jb.eligibility_notes,
    jb.amount_min_cents,
    jb.amount_max_cents,
    jb.effective_date               AS benefit_effective_date,
    str.tax_year,
    str.military_retirement_exempt,
    str.va_disability_exempt,
    sub.status                      AS subscription_status,
    sub.current_period_end          AS subscription_renews_at
FROM users u
LEFT JOIN user_profiles up ON up.user_id = u.id
LEFT JOIN jurisdictions j ON j.id = up.preferred_jurisdiction_id
LEFT JOIN jurisdiction_benefits jb ON jb.jurisdiction_id = j.id
LEFT JOIN benefits b ON b.id = jb.benefit_id
LEFT JOIN state_tax_rules str ON str.jurisdiction_id = j.id
    AND str.tax_year = EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER
LEFT JOIN subscriptions sub ON sub.user_id = u.id
    AND sub.status IN ('active', 'trialing')
WHERE u.deleted_at IS NULL
  AND u.is_active = TRUE;

COMMENT ON VIEW user_benefits_dashboard_view IS
    'User-centric benefits dashboard joining jurisdiction benefits, tax rules, and subscription';

-- -----------------------------------------------------------------------------
-- state_comparison_view
-- Side-by-side jurisdiction comparison for state benefits explorer.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW state_comparison_view AS
SELECT
    j.id                            AS jurisdiction_id,
    j.name                          AS jurisdiction_name,
    j.abbreviation,
    j.is_state,
    j.is_territory,
    j.veteran_population_estimate,
    b.id                            AS benefit_id,
    b.code                          AS benefit_code,
    b.name                          AS benefit_name,
    b.category,
    b.is_federal,
    jb.is_available,
    jb.eligibility_notes,
    jb.amount_min_cents,
    jb.amount_max_cents,
    jb.source_url                   AS benefit_source_url,
    str.tax_year,
    str.military_retirement_exempt,
    str.va_disability_exempt,
    str.partial_exemption_notes,
    arm.metric_key                  AS alabama_metric_key,
    arm.metric_value                AS alabama_metric_value,
    arm.rank_national               AS alabama_rank_national
FROM jurisdictions j
LEFT JOIN jurisdiction_benefits jb ON jb.jurisdiction_id = j.id
LEFT JOIN benefits b ON b.id = jb.benefit_id
LEFT JOIN state_tax_rules str ON str.jurisdiction_id = j.id
    AND str.tax_year = EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER
LEFT JOIN alabama_ranking_metrics arm ON j.abbreviation = 'AL'
    AND arm.data_year = EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER
ORDER BY j.abbreviation, b.category, b.name;

COMMENT ON VIEW state_comparison_view IS
    'Multi-jurisdiction benefit and tax comparison for the state explorer UI';
