-- 0003 Consent (Privacy & Consent Guardian, deterministic).
--
-- Consent is purpose-scoped and revocable. Purposes form an allowlist; nine
-- purposes are FORECLOSED: no user, admin, or the schema owner can record
-- consent to them (closes CB-03, where foreclosed purposes were storable). The
-- CHECK constraint, not application code, is what refuses them.
--
-- Revocation is immediate: protected rows (0004) are visible only while an
-- active consent exists, checked inside the same transaction as the read.

CREATE TABLE vb.consent_purposes (
  purpose      text PRIMARY KEY,
  description  text NOT NULL,
  foreclosed   boolean NOT NULL DEFAULT false
);

INSERT INTO vb.consent_purposes (purpose, description, foreclosed) VALUES
  ('plan_storage',              'Save my Mission Brief, case and tasks in my private account (Privacy Mode B).', false),
  ('advertising',               'Use my data to show me or others advertising.', true),
  ('ad_targeting',              'Build an advertising or marketing profile about me.', true),
  ('data_sale',                 'Sell or license my data.', true),
  ('model_training',            'Train or fine-tune an AI model on my data.', true),
  ('claims_company_sharing',    'Share my data with a claims consultant or claims company.', true),
  ('lender_sharing',            'Share my data with a lender.', true),
  ('recruiter_sharing',         'Share my data with a recruiter or employer without a per-recipient request.', true),
  ('data_broker_sharing',       'Share my data with a data broker.', true),
  ('bulk_research_export',      'Export identifiable records in bulk for research.', true);

ALTER TABLE vb.consent_purposes ENABLE ROW LEVEL SECURITY;
ALTER TABLE vb.consent_purposes FORCE ROW LEVEL SECURITY;
CREATE POLICY consent_purposes_read ON vb.consent_purposes FOR SELECT TO vetbuddy_app USING (true);
GRANT SELECT ON vb.consent_purposes TO vetbuddy_app;

-- The allowlist, as a constraint that holds for every role. Kept in step with
-- consent_purposes by tests/test_consent.py.
CREATE TABLE vb.consents (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       uuid NOT NULL,
  user_id         uuid NOT NULL,
  purpose         text NOT NULL REFERENCES vb.consent_purposes(purpose)
                  CONSTRAINT consent_purpose_allowed CHECK (purpose IN ('plan_storage')),
  policy_version  text NOT NULL,
  granted_at      timestamptz NOT NULL DEFAULT now(),
  revoked_at      timestamptz,
  FOREIGN KEY (tenant_id, user_id) REFERENCES vb.users(tenant_id, id),
  CHECK (revoked_at IS NULL OR revoked_at >= granted_at)
);

-- At most one active consent per user and purpose.
CREATE UNIQUE INDEX consents_one_active ON vb.consents (tenant_id, user_id, purpose) WHERE revoked_at IS NULL;

ALTER TABLE vb.consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE vb.consents FORCE ROW LEVEL SECURITY;

CREATE POLICY consents_self ON vb.consents FOR ALL TO vetbuddy_app
  USING (tenant_id = vb.current_tenant() AND user_id = vb.current_user_id())
  WITH CHECK (tenant_id = vb.current_tenant() AND user_id = vb.current_user_id());

GRANT SELECT, INSERT ON vb.consents TO vetbuddy_app;
-- Only the revocation timestamp may change; consent history is never deleted.
GRANT UPDATE (revoked_at) ON vb.consents TO vetbuddy_app;

CREATE OR REPLACE FUNCTION vb.has_consent(p_purpose text) RETURNS boolean
  LANGUAGE sql STABLE AS $$
  SELECT EXISTS (
    SELECT 1 FROM vb.consents c
     WHERE c.tenant_id = vb.current_tenant()
       AND c.user_id = vb.current_user_id()
       AND c.purpose = p_purpose
       AND c.revoked_at IS NULL)
$$;

GRANT EXECUTE ON FUNCTION vb.has_consent(text) TO vetbuddy_app;
