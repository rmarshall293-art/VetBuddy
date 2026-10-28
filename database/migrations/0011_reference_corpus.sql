-- 0011 — Plane 4 reference corpus (slice 02).
--
-- A separate `ref` schema for V0 PUBLIC reference data: no tenant, no person,
-- no RLS (nothing in it is about a user). It holds LEADS and CONTEXT with
-- provenance — the research reports, Sentinel, the Women Veterans module and
-- the Education Navigator registry — never an eligibility rule. Eligibility
-- stays in public.benefit / eligibility_rule behind a named human verifier (G1).
--
-- Why not reuse public.resource / installation / source_record: those are
-- tenant-scoped (organization-curated, RLS-forced). Global reference data in
-- a tenant table would be duplicated per tenant or leak across them.
--
-- Rows are written only by the schema owner through scripts/build_reference.py
-- (generated database/seeds/0011_reference.sql). The app role reads only.

CREATE SCHEMA ref;

-- One status vocabulary for every reference row. VERIFIED needs a named human
-- and a date (CHECK on each table); a seed script cannot supply either.
CREATE DOMAIN ref.record_status AS TEXT
  CHECK (VALUE IN ('UNVERIFIED','SOURCE_CHECKED','CONTESTED','SUPERSEDED',
                   'VERIFIED','ILLUSTRATIVE','HEURISTIC'));

CREATE TABLE ref.source (
  source_id  TEXT PRIMARY KEY CHECK (source_id ~ '^src\.[a-z0-9_.]+$'),
  title      TEXT NOT NULL,
  kind       TEXT NOT NULL CHECK (kind IN ('research_report','module_source','module_spec',
                                           'governance','legacy_build','primary')),
  tier       SMALLINT CHECK (tier BETWEEN 1 AND 4),
  as_of      DATE NOT NULL,
  origin     TEXT NOT NULL,
  note       TEXT,
  CHECK (kind = 'governance' OR tier IS NOT NULL)
);

CREATE TABLE ref.dataset (
  dataset_id    TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  version       TEXT NOT NULL,
  as_of         DATE NOT NULL,
  review_by     DATE,
  sha256        TEXT NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  record_count  INTEGER NOT NULL CHECK (record_count >= 0)
);

-- Every row names at least one registered source (rule R6 / T0-06 at rest).
CREATE FUNCTION ref.assert_sources() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE missing TEXT[];
BEGIN
  IF NEW.source_ids IS NULL OR cardinality(NEW.source_ids) = 0 THEN
    RAISE EXCEPTION 'ref row % has no source', TG_TABLE_NAME;
  END IF;
  SELECT array_agg(s) INTO missing FROM unnest(NEW.source_ids) s
   WHERE NOT EXISTS (SELECT 1 FROM ref.source r WHERE r.source_id = s);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'ref row in % cites unregistered source(s): %', TG_TABLE_NAME, missing;
  END IF;
  RETURN NEW;
END $$;

CREATE TABLE ref.care_type (
  code   TEXT PRIMARY KEY CHECK (code ~ '^wv_[a-z_]+$'),
  label  TEXT NOT NULL
);

CREATE TABLE ref.directory_entry (
  entry_id          TEXT PRIMARY KEY,
  kind              TEXT NOT NULL CHECK (kind IN ('national','state_office','facility_role',
                                                  'territory_dv_coalition','mst_residential','clinic')),
  jurisdiction_code TEXT NOT NULL REFERENCES public.jurisdiction(code),
  name              TEXT NOT NULL,
  place             TEXT,
  org_type          TEXT,
  program           TEXT,
  care_types        TEXT[] NOT NULL DEFAULT '{}',
  phone             TEXT,
  phone_e164        TEXT,
  text_line         TEXT,
  mailbox           TEXT,
  url               TEXT,
  eligibility_note  TEXT,
  caveat            TEXT,
  dedicated_coordinator BOOLEAN,
  also_in_crisis_floor  TEXT,
  last_checked      DATE,
  status            ref.record_status NOT NULL,
  source_ids        TEXT[] NOT NULL,
  verified_by       TEXT,
  verified_on       DATE,
  CHECK (status <> 'VERIFIED' OR (verified_by IS NOT NULL AND verified_on IS NOT NULL)),
  -- The retired Veterans Crisis Line number must never be stored as live.
  CHECK (phone_e164 IS DISTINCT FROM '+18002738255'),
  CHECK (url IS NULL OR url ~ '^https://')
);
-- Dedupe key: organization + place, never phone alone (WV defect A-7).
CREATE UNIQUE INDEX directory_entry_natural_key
  ON ref.directory_entry (kind, jurisdiction_code, lower(name), coalesce(lower(place), ''));
CREATE INDEX directory_entry_jur ON ref.directory_entry (jurisdiction_code, kind);
CREATE INDEX directory_entry_care ON ref.directory_entry USING GIN (care_types);

CREATE FUNCTION ref.assert_care_types() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM unnest(NEW.care_types) c
              WHERE NOT EXISTS (SELECT 1 FROM ref.care_type t WHERE t.code = c)) THEN
    RAISE EXCEPTION 'unknown care_type in %', NEW.care_types;
  END IF;
  RETURN NEW;
END $$;

CREATE TABLE ref.conflict (
  conflict_id  TEXT PRIMARY KEY CHECK (conflict_id ~ '^conflict\.'),
  subject      TEXT NOT NULL,
  status       TEXT NOT NULL CHECK (status IN ('contested_unresolved','resolved_by_design')),
  readings     JSONB NOT NULL CHECK (jsonb_typeof(readings) = 'array' AND jsonb_array_length(readings) >= 2),
  why_it_matters TEXT,
  next_action  TEXT,
  resolution   TEXT,
  blocking_for TEXT[] NOT NULL DEFAULT '{}',
  source_ids   TEXT[] NOT NULL,
  -- A conflict is surfaced, never silently resolved.
  CHECK (status <> 'resolved_by_design' OR resolution IS NOT NULL)
);

CREATE TABLE ref.supersession (
  supersession_id TEXT PRIMARY KEY,
  old_value  TEXT NOT NULL,
  new_value  TEXT NOT NULL,
  effective  TEXT,
  note       TEXT,
  source_ids TEXT[] NOT NULL
);

CREATE TABLE ref.statistic (
  stat_id           TEXT PRIMARY KEY,
  jurisdiction_code TEXT NOT NULL REFERENCES public.jurisdiction(code),
  metric            TEXT NOT NULL,
  value             TEXT NOT NULL,
  unit              TEXT NOT NULL,
  period            TEXT NOT NULL,
  note              TEXT,
  conflict_id       TEXT REFERENCES ref.conflict(conflict_id),
  status            ref.record_status NOT NULL,
  source_ids        TEXT[] NOT NULL,
  CHECK (status <> 'VERIFIED')
);

-- Money is integer cents (P8). Kernels may read only rows a human verified;
-- ILLUSTRATIVE and HEURISTIC rows exist for explainers and can never be used.
CREATE TABLE ref.rate (
  rate_set        TEXT NOT NULL,
  dims            JSONB NOT NULL,
  amount_cents    BIGINT NOT NULL CHECK (amount_cents >= 0),
  rounded         BOOLEAN NOT NULL DEFAULT false,
  effective_from  DATE NOT NULL,
  effective_to    DATE,
  note            TEXT,
  conflict_id     TEXT REFERENCES ref.conflict(conflict_id),
  status          ref.record_status NOT NULL,
  source_ids      TEXT[] NOT NULL,
  verified_by     TEXT,
  verified_on     DATE,
  PRIMARY KEY (rate_set, dims),
  CHECK (effective_to IS NULL OR effective_to >= effective_from),
  CHECK (status <> 'VERIFIED' OR (verified_by IS NOT NULL AND verified_on IS NOT NULL AND NOT rounded))
);

CREATE TABLE ref.state_summary (
  jurisdiction_code TEXT PRIMARY KEY REFERENCES public.jurisdiction(code),
  military_retirement_tax TEXT NOT NULL CHECK (military_retirement_tax IN ('full_exempt','partial','no_income_tax')),
  no_state_income_tax BOOLEAN NOT NULL,
  disabled_veteran_property_tax TEXT NOT NULL,
  notable_programs  TEXT,
  status            ref.record_status NOT NULL,
  source_ids        TEXT[] NOT NULL,
  CHECK (status <> 'VERIFIED'),
  CHECK (no_state_income_tax = (military_retirement_tax = 'no_income_tax'))
);

-- Leads are never verified here: verification lives on a rule pack, with a
-- named reviewer, in public.benefit / eligibility_rule.
CREATE TABLE ref.benefit_lead (
  lead_id           TEXT PRIMARY KEY,
  jurisdiction_code TEXT NOT NULL REFERENCES public.jurisdiction(code),
  category          TEXT NOT NULL CHECK (category IN ('income','property','edu_member','edu_family',
                                                      'employ','rec','vehicle','biz','retire')),
  text              TEXT NOT NULL,
  authority         TEXT NOT NULL,
  note              TEXT,
  conflict_id       TEXT REFERENCES ref.conflict(conflict_id),
  status            ref.record_status NOT NULL,
  source_ids        TEXT[] NOT NULL,
  CHECK (status <> 'VERIFIED'),
  CHECK (status <> 'CONTESTED' OR conflict_id IS NOT NULL)
);

CREATE TABLE ref.duty_authority (
  authority_id   TEXT PRIMARY KEY,
  citation       TEXT NOT NULL,
  label          TEXT NOT NULL,
  qualifies_ch33 BOOLEAN NOT NULL,
  tier_caveat    BOOLEAN NOT NULL DEFAULT false,
  guard_only     BOOLEAN NOT NULL DEFAULT false,
  coast_guard_only BOOLEAN NOT NULL DEFAULT false,
  status         ref.record_status NOT NULL,
  source_ids     TEXT[] NOT NULL
);

CREATE TABLE ref.rule_lead (
  lead_id    TEXT PRIMARY KEY,
  domain     TEXT NOT NULL,
  benefit    TEXT NOT NULL,
  citation   TEXT NOT NULL,
  lead       TEXT NOT NULL,
  caveat     TEXT,
  status     ref.record_status NOT NULL,
  source_ids TEXT[] NOT NULL,
  CHECK (status <> 'VERIFIED')
);

CREATE TABLE ref.timeline_window (
  window_id      TEXT PRIMARY KEY,
  kind           TEXT NOT NULL CHECK (kind IN ('statutory_window','program_window','limit')),
  anchor         TEXT NOT NULL,
  offset_text    TEXT NOT NULL,
  item           TEXT NOT NULL,
  verify_against TEXT NOT NULL,   -- a deadline must name the authority it rests on
  status         ref.record_status NOT NULL,
  source_ids     TEXT[] NOT NULL,
  verified_by    TEXT,
  verified_on    DATE,
  CHECK (status <> 'VERIFIED' OR (verified_by IS NOT NULL AND verified_on IS NOT NULL))
);

CREATE TABLE ref.education_program (
  program_id        TEXT PRIMARY KEY,
  name              TEXT NOT NULL,
  authority         TEXT NOT NULL,
  carried_by        TEXT[] NOT NULL,
  stacking_notes    TEXT,
  note              TEXT,
  is_authority_stub BOOLEAN NOT NULL DEFAULT true,
  status            ref.record_status NOT NULL,
  source_ids        TEXT[] NOT NULL,
  CHECK (cardinality(carried_by) > 0)
);
CREATE UNIQUE INDEX education_program_name ON ref.education_program (lower(name));

CREATE TABLE ref.installation (
  installation_id   TEXT PRIMARY KEY,
  jurisdiction_code TEXT NOT NULL REFERENCES public.jurisdiction(code),
  name              TEXT NOT NULL,
  place             TEXT,
  branch            TEXT NOT NULL,
  role              TEXT,
  approx_population TEXT,
  tap_delivery      TEXT,
  former_name       TEXT,
  status            ref.record_status NOT NULL,
  source_ids        TEXT[] NOT NULL
);

CREATE TABLE ref.finding (
  finding_id        TEXT PRIMARY KEY,
  kind              TEXT NOT NULL CHECK (kind IN ('state_program','peer_flagship','oversight_finding',
                                                  'what_works','policy_event','product_implication',
                                                  'preparation_step','data_maintenance')),
  jurisdiction_code TEXT REFERENCES public.jurisdiction(code),
  title             TEXT NOT NULL,
  detail            TEXT NOT NULL,
  event_date        TEXT CHECK (event_date IS NULL OR event_date ~ '^\d{4}(-\d{2}(-\d{2})?)?$'),
  status            ref.record_status NOT NULL,
  source_ids        TEXT[] NOT NULL
);

CREATE TABLE ref.governance_rule (
  rule_id      TEXT PRIMARY KEY,
  family       TEXT NOT NULL CHECK (family IN ('non_negotiable','tier0','agent_rule','release_gate')),
  text         TEXT NOT NULL,
  enforced_by  TEXT,
  on_violation TEXT,
  repo_status  TEXT CHECK (repo_status IN ('IMPLEMENTED_VERIFIED','IMPLEMENTED_UNTESTED','PARTIAL','MOCK',
                                           'NOT_PRESENT','BLOCKED_SOURCE','DEFERRED')),
  note         TEXT,
  source_ids   TEXT[] NOT NULL
);

CREATE TABLE ref.module (
  module_id  TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  plane_fit  TEXT NOT NULL,
  integrated TEXT[] NOT NULL DEFAULT '{}',
  spec_only  TEXT[] NOT NULL DEFAULT '{}',
  counts     JSONB NOT NULL DEFAULT '{}',
  source_ids TEXT[] NOT NULL
);

-- Source triggers on every table that carries source_ids.
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT c.table_name FROM information_schema.columns c
            WHERE c.table_schema = 'ref' AND c.column_name = 'source_ids'
  LOOP
    EXECUTE format('CREATE TRIGGER %I BEFORE INSERT OR UPDATE ON ref.%I
                    FOR EACH ROW EXECUTE FUNCTION ref.assert_sources()', t || '_sources', t);
  END LOOP;
END $$;
CREATE TRIGGER directory_entry_care_types BEFORE INSERT OR UPDATE ON ref.directory_entry
  FOR EACH ROW EXECUTE FUNCTION ref.assert_care_types();

-- Coverage ledger: what the corpus holds per jurisdiction, beside the
-- jurisdiction's verification status. Gaps are visible, not inferred.
CREATE VIEW ref.v_coverage AS
SELECT j.code, j.name, j.kind, j.verification_status,
       (SELECT count(*) FROM ref.directory_entry d WHERE d.jurisdiction_code = j.code) AS directory_entries,
       (SELECT count(*) FROM ref.benefit_lead b WHERE b.jurisdiction_code = j.code)    AS benefit_leads,
       (SELECT count(*) FROM ref.benefit_lead b WHERE b.jurisdiction_code = j.code AND b.status = 'CONTESTED') AS contested_leads,
       EXISTS (SELECT 1 FROM ref.state_summary s WHERE s.jurisdiction_code = j.code)  AS has_financial_summary,
       (SELECT count(*) FROM ref.statistic s WHERE s.jurisdiction_code = j.code)       AS statistics
  FROM public.jurisdiction j;

-- Status posture per table: the honest picture in one query.
CREATE VIEW ref.v_status_posture AS
SELECT 'directory_entry' AS tbl, status::text, count(*) FROM ref.directory_entry GROUP BY status
UNION ALL SELECT 'benefit_lead', status::text, count(*) FROM ref.benefit_lead GROUP BY status
UNION ALL SELECT 'rate', status::text, count(*) FROM ref.rate GROUP BY status
UNION ALL SELECT 'statistic', status::text, count(*) FROM ref.statistic GROUP BY status
UNION ALL SELECT 'rule_lead', status::text, count(*) FROM ref.rule_lead GROUP BY status
UNION ALL SELECT 'timeline_window', status::text, count(*) FROM ref.timeline_window GROUP BY status;

-- Zero-PII guard for the reference schema (carry-back CB-07 shape): fail the
-- migration if any ref table grows a tenant/person/contact-identity column.
DO $$
DECLARE bad TEXT;
BEGIN
  SELECT string_agg(table_name || '.' || column_name, ', ') INTO bad
    FROM information_schema.columns
   WHERE table_schema = 'ref'
     AND column_name IN ('tenant_id','person_id','user_id','email','ssn','dob','date_of_birth',
                         'first_name','last_name','contact_name','staff_name');
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'ref schema must hold no person or tenant columns: %', bad;
  END IF;
END $$;

-- The app role reads; it never writes reference data.
GRANT USAGE ON SCHEMA ref TO vetbuddy_app;
GRANT SELECT ON ALL TABLES IN SCHEMA ref TO vetbuddy_app;
