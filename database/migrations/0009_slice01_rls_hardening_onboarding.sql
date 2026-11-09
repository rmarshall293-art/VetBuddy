-- 0009 — Slice 01 hardening + onboarding/mission support.
--
-- Found by applying 0001–0008 to a real PostgreSQL 16 (2026-10-20) and
-- probing as a non-owner role (see docs/CURRENT_STATE_AUDIT.md):
--   F1  household had tenant_id but RLS was OFF  -> cross-tenant read.
--   F2  tenant table had RLS OFF.
--   F3  no table used FORCE ROW LEVEL SECURITY -> table owner bypasses all
--       policies; a backend connecting as owner had NO isolation.
--   F4  policies used current_setting('vetbuddy.tenant_id') without
--       missing_ok -> unset context raised an error instead of failing closed
--       to zero rows.
--   F5  policies had no explicit WITH CHECK.
--   F6  four agent manifests seeded as PRODUCTION with empty data classes /
--       tools — contradicts "no manifest, no access" and the Merged
--       Blueprint statement that no agent is in production.
-- 0001–0008 are left untouched (preserve rule); this file supersedes their
-- policies.

-- ── Runtime role ──────────────────────────────────────────────────────────
-- The API connects as a LOGIN role that is a member of vetbuddy_app. That
-- role never owns tables, so RLS always applies to it.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vetbuddy_app') THEN
    CREATE ROLE vetbuddy_app NOLOGIN;
  END IF;
END $$;

-- Fail-closed tenant accessor: unset or empty -> NULL -> matches no row.
CREATE OR REPLACE FUNCTION vb_current_tenant() RETURNS uuid
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('vetbuddy.tenant_id', true), '')::uuid
$$;

-- ── Slice 01 schema additions ─────────────────────────────────────────────
-- Privacy mode C is unreachable without an explicit, reviewed flag
-- (Merged Blueprint §1.1 "managed_requires_flag").
ALTER TABLE app_user ADD COLUMN managed_case_enabled BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE app_user ADD CONSTRAINT managed_requires_flag
  CHECK (privacy_mode <> 'C' OR managed_case_enabled);

-- Consent purposes are an allowlist. A purpose not in this table cannot be
-- stored at all (closes the "foreclosed purposes are storable" class of
-- defect, CB-03, by construction rather than by a denylist we do not have
-- the source text for).
CREATE TABLE consent_purpose (
  purpose      TEXT PRIMARY KEY,
  description  TEXT NOT NULL,
  data_classes TEXT[] NOT NULL,
  allowed      BOOLEAN NOT NULL DEFAULT true
);
INSERT INTO consent_purpose (purpose, description, data_classes) VALUES
 ('personal_mission_planning',
  'Store my profile, service context, mission, cases and tasks so VetBuddy can build my Mission Brief. Not shared with anyone.',
  ARRAY['V1','V2']);
ALTER TABLE consent_record
  ADD CONSTRAINT consent_purpose_fk FOREIGN KEY (purpose) REFERENCES consent_purpose(purpose);

-- Service facts carry provenance; Guard/Reserve status is never inferred
-- from component alone (v4.0 §34; Sentinel: "the citation block on your
-- orders is the determinative artifact").
ALTER TABLE service_record
  ADD COLUMN fact_status TEXT NOT NULL DEFAULT 'DECLARED'
    CHECK (fact_status IN ('DECLARED','EXTRACTED_UNCONFIRMED','VERIFIED')),
  ADD CONSTRAINT branch_known CHECK (branch IN
    ('Army','Navy','Marine Corps','Air Force','Space Force','Coast Guard')),
  ADD CONSTRAINT legal_authority_vocab CHECK (legal_authority IS NULL OR legal_authority IN
    ('title_10','title_32','state_active_duty','idt_annual_training','not_applicable','unknown')),
  ADD CONSTRAINT guard_reserve_needs_authority CHECK (
    component NOT IN ('national_guard','reserve') OR legal_authority IS NOT NULL);

-- Mission keeps the deterministic router's input snapshot + output so a
-- brief is reproducible and auditable (v4.0 §18).
ALTER TABLE mission
  ADD COLUMN goals TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN router_input JSONB,
  ADD COLUMN router_input_hash TEXT,
  ADD COLUMN brief JSONB;

ALTER TABLE task
  ADD COLUMN template_id TEXT,
  ADD COLUMN readiness_dimension TEXT CHECK (readiness_dimension IN
    ('documents','benefits','claims_evidence','coverage','career','education',
     'financial','housing_relocation','family','community')),
  ADD COLUMN completed_at TIMESTAMPTZ,
  ADD COLUMN version INTEGER NOT NULL DEFAULT 1;   -- optimistic concurrency

-- Transactional outbox (master spec §8). Written in the same transaction as
-- the domain change. No consumer ships in slice 01 (status: PARTIAL).
CREATE TABLE outbox_event (
  event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
  schema_version  TEXT NOT NULL DEFAULT 'vetbuddy.event.v1',
  event_type      TEXT NOT NULL CHECK (event_type IN (
                    'PROFILE_COMPLETED','TRANSITION_STAGE_CHANGED','MISSION_CREATED','CASE_CREATED',
                    'TASK_CREATED','TASK_COMPLETED','CONSENT_UPDATED','HUMAN_REVIEW_REQUIRED')),
  aggregate_type  TEXT NOT NULL,
  aggregate_id    UUID NOT NULL,
  actor_user_id   UUID REFERENCES app_user(user_id),
  correlation_id  TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  classification  TEXT NOT NULL DEFAULT 'V1',
  payload         JSONB NOT NULL,          -- references only, never raw PII
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at    TIMESTAMPTZ,
  UNIQUE (tenant_id, idempotency_key)
);

-- ── F6: no agent is in production ─────────────────────────────────────────
UPDATE agent_manifest SET status = 'DRAFT'
 WHERE status = 'PRODUCTION'
   AND (cardinality(readable_data_classes) = 0 OR cardinality(approved_tools) = 0);

-- ── F1–F5: uniform, forced, fail-closed tenant isolation ──────────────────
DO $$
DECLARE r RECORD; p RECORD;
BEGIN
  FOR r IN
    SELECT c.relname FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind = 'r'
      AND EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = 'public' AND table_name = c.relname
                    AND column_name = 'tenant_id')
  LOOP
    FOR p IN SELECT polname FROM pg_policy WHERE polrelid = format('public.%I', r.relname)::regclass LOOP
      EXECUTE format('DROP POLICY %I ON %I', p.polname, r.relname);
    END LOOP;
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', r.relname);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', r.relname);
    EXECUTE format('CREATE POLICY tenant_isolation ON %I USING (tenant_id = vb_current_tenant()) '
                   'WITH CHECK (tenant_id = vb_current_tenant())', r.relname);
  END LOOP;
END $$;

-- ── Grants: least privilege, no DELETE anywhere, audit is insert-only ─────
GRANT USAGE ON SCHEMA public TO vetbuddy_app;
GRANT SELECT ON jurisdiction, eligibility_rule, mos_crosswalk, agent_manifest, consent_purpose
  TO vetbuddy_app;
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN
    SELECT table_name FROM information_schema.columns
    WHERE table_schema = 'public' AND column_name = 'tenant_id'
  LOOP
    EXECUTE format('GRANT SELECT, INSERT ON %I TO vetbuddy_app', r.table_name);
    IF r.table_name NOT IN ('audit_event','outbox_event','tenant') THEN
      EXECUTE format('GRANT UPDATE ON %I TO vetbuddy_app', r.table_name);
    END IF;
  END LOOP;
END $$;

-- ── Guard: "a table with RLS on and no policy is invisible, not secure",
--    and a tenant table without FORCE RLS is not isolated. Fail the
--    migration rather than ship either state. ────────────────────────────────
DO $$
DECLARE bad TEXT;
BEGIN
  SELECT string_agg(c.relname, ', ') INTO bad
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'public' AND c.relkind = 'r'
    AND (
      (c.relrowsecurity AND NOT EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid = c.oid))
      OR (EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema='public' AND table_name=c.relname AND column_name='tenant_id')
          AND NOT (c.relrowsecurity AND c.relforcerowsecurity))
    );
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'RLS guard failed for: %', bad;
  END IF;
END $$;
