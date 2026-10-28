-- 0014_benefit_vault.sql
--
-- Benefit Vault: read-only reference tables generated from
-- data/reference/benefit_vault_registry.json (seed: database/seeds/0014_benefit_vault_seed.sql),
-- and three tenant tables: pull grants, the hash-chained pull ledger, and
-- saved benefits.
--
-- Rules carried from earlier migrations (integrated onto slice 03, ADR 0005):
--   * 0009/0013: every public table that can hold a person's data has a NOT
--     NULL tenant_id referencing public.tenant, forced row-level security with
--     a policy, and no DELETE or TRUNCATE grant for vetbuddy_app.
--   * 0013: account deletion is vb_delete_account(), run as the NOLOGIN,
--     NOBYPASSRLS role vetbuddy_purger. It deletes from every public table with
--     a tenant_id, so it reaches these three tables, provided vetbuddy_purger
--     holds SELECT and DELETE on them (granted below; the postcondition fails
--     the migration if any tenant table lacks the grant).
--   * 0013: append-only tables allow DELETE only for the tenant being purged:
--     vetbuddy.purge_tenant is set transaction-locally by vb_delete_account and
--     the deleting role must be vetbuddy_purger.
--   (The package was first built against a sandbox stand-in with a
--   privacy.deletion_job / privacy.purge design; slice 03 has neither, so those
--   references were replaced here. See docs/ADR/0005.)
--   * Master Prompt v6: agents never decide. Every manifest is pinned to
--     may_issue_determinations = false, and only benefit_vault_agent may pull
--     from other agents (pinned four ways: JSON Schema, loader, here, tests).
--   * VERIFIED needs a named reviewer and holds only while the reviewed
--     content is unchanged (gate G1). The reviewer is recorded by a roster
--     handle, never a personal name or email address.
--
-- Apply after 0013 and before the seed, in one transaction.

-- ── reference tables (read-only for the app) ──────────────────────────────

CREATE TABLE ref.vault_registry_meta (
  singleton  BOOLEAN PRIMARY KEY DEFAULT true CHECK (singleton),
  registry   TEXT NOT NULL CHECK (registry = 'vetbuddy.benefit_vault_registry'),
  version    TEXT NOT NULL CHECK (version ~ '^\d+\.\d+\.\d+$'),
  as_of      DATE NOT NULL,
  sha256     TEXT NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  notice     TEXT NOT NULL CHECK (length(notice) BETWEEN 1 AND 1200)
);

CREATE TABLE ref.vault_jurisdiction (
  code               TEXT PRIMARY KEY CHECK (code ~ '^[A-Z]{2}$'),
  name               TEXT NOT NULL,
  coverage           TEXT NOT NULL CHECK (coverage IN ('COVERED','SOURCE_NOT_AVAILABLE')),
  benefit_count      INTEGER NOT NULL CHECK (benefit_count >= 0),
  tail_unread_chars  INTEGER NOT NULL DEFAULT 0 CHECK (tail_unread_chars >= 0),
  registry_sha256    TEXT NOT NULL CHECK (registry_sha256 ~ '^[0-9a-f]{64}$'),
  CONSTRAINT covered_has_records CHECK ((coverage = 'COVERED') = (benefit_count > 0))
);

CREATE TABLE ref.vault_source (
  source_id          TEXT PRIMARY KEY CHECK (source_id ~ '^src\.[a-z0-9.-]+$'),
  url                TEXT CHECK (url IS NULL OR url ~ '^https://[^\s|]+$'),
  page_status        TEXT NOT NULL CHECK (page_status IN ('OPENED','SEEN_IN_SEARCH')),
  tier               SMALLINT NOT NULL CHECK (tier BETWEEN 1 AND 4),
  opened_on          DATE,
  seen_on            DATE,
  page_updated       DATE,
  tail_unread_chars  INTEGER NOT NULL DEFAULT 0 CHECK (tail_unread_chars >= 0),
  registry_sha256    TEXT NOT NULL CHECK (registry_sha256 ~ '^[0-9a-f]{64}$'),
  CONSTRAINT opened_has_url CHECK ((page_status = 'OPENED') = (url IS NOT NULL)),
  CONSTRAINT opened_has_date CHECK (page_status <> 'OPENED' OR opened_on IS NOT NULL),
  CONSTRAINT seen_has_date CHECK (page_status <> 'SEEN_IN_SEARCH' OR (seen_on IS NOT NULL AND tier = 4))
);

CREATE TABLE ref.vault_fact (
  fact_key      TEXT PRIMARY KEY CHECK (fact_key ~ '^[a-z][a-z_]{1,60}$'),
  data_class    TEXT NOT NULL CHECK (data_class IN ('V0','V1','V2','V3','V4','V5')),
  kind          TEXT NOT NULL CHECK (kind IN ('enum','bool','int','rating','jurisdiction')),
  question      TEXT NOT NULL,
  session_only  BOOLEAN NOT NULL,
  pullable      BOOLEAN NOT NULL,
  registry_sha256 TEXT NOT NULL CHECK (registry_sha256 ~ '^[0-9a-f]{64}$'),
  CONSTRAINT high_classes_never_travel CHECK (data_class NOT IN ('V3','V4','V5') OR NOT pullable),
  CONSTRAINT session_only_never_travels CHECK (NOT session_only OR NOT pullable)
);

CREATE TABLE ref.vault_benefit (
  benefit_id            TEXT PRIMARY KEY CHECK (benefit_id ~ '^[a-z]{2}\.[a-z0-9-]{1,80}$'),
  jurisdiction          TEXT NOT NULL REFERENCES ref.vault_jurisdiction (code),
  category              TEXT NOT NULL CHECK (category IN (
                          'INCTAX','PROPTAX','PLATES','GUARD_EDU','EDU','JOBS','GUARD_PAY','HUNTFISH','PARKS','HOMES',
                          'BURIAL','BONUS','OTHER','SCHOLARSHIP','PASS','TICKETS','DEALS','TRAVEL','MWR','HEALTH',
                          'HOUSING','INSURANCE','FAMILY','LICENSE')),
  kind                  TEXT NOT NULL CHECK (kind IN ('STATE_BENEFIT','FEDERAL_BENEFIT','NONPROFIT_PROGRAM','COMMERCIAL_DEAL')),
  title                 TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 140),
  groups                TEXT[] NOT NULL CHECK (cardinality(groups) >= 1 AND groups <@ ARRAY['ad','ng','rsv','vet','dv','ret','sp','ch','ss','gs','sm','all']::TEXT[]),
  rule                  TEXT NOT NULL CHECK (rule ~ '^[a-z0-9 &|!()<>=]+$'),
  rule_tokens           TEXT[] NOT NULL CHECK (cardinality(rule_tokens) >= 1),
  who_it_is_for         TEXT NOT NULL CHECK (length(who_it_is_for) BETWEEN 1 AND 280),
  value                 TEXT NOT NULL CHECK (length(value) BETWEEN 1 AND 240),
  official_url          TEXT NOT NULL CHECK (official_url ~ '^https://[^\s|]+$'),
  official_url_status   TEXT NOT NULL CHECK (official_url_status IN ('SAME_AS_SOURCE','LINKED_FROM_SOURCE','SEEN_IN_SEARCH')),
  source_id             TEXT NOT NULL REFERENCES ref.vault_source (source_id),
  source_tier           SMALLINT NOT NULL CHECK (source_tier BETWEEN 1 AND 4),
  record_status         TEXT NOT NULL CHECK (record_status IN
                          ('UNVERIFIED','SOURCE_CHECKED','CONTESTED','SUPERSEDED','ILLUSTRATIVE','HEURISTIC','VERIFIED')),
  content_hash          TEXT NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
  ledger_ref            TEXT NOT NULL CHECK (ledger_ref ~ '^(states|federal)/[A-Za-z0-9_.-]+\.psv:\d+$'),
  verified_by           TEXT CHECK (verified_by IS NULL OR verified_by ~ '^[a-z0-9][a-z0-9._-]{1,63}$'),
  verified_on           DATE,
  verified_content_hash TEXT,
  registry_sha256       TEXT NOT NULL CHECK (registry_sha256 ~ '^[0-9a-f]{64}$'),
  CONSTRAINT verified_needs_named_reviewer CHECK (
    record_status <> 'VERIFIED'
    OR (verified_by IS NOT NULL AND btrim(verified_by) <> '' AND verified_on IS NOT NULL
        AND verified_content_hash = content_hash)),
  CONSTRAINT unverified_has_no_reviewer CHECK (
    record_status = 'VERIFIED' OR (verified_by IS NULL AND verified_on IS NULL AND verified_content_hash IS NULL)),
  CONSTRAINT state_records_are_state_benefits CHECK (
    jurisdiction = 'US'
    OR (kind = 'STATE_BENEFIT' AND category IN ('INCTAX','PROPTAX','PLATES','GUARD_EDU','EDU','JOBS','GUARD_PAY',
                                                 'HUNTFISH','PARKS','HOMES','BURIAL','BONUS','OTHER'))),
  CONSTRAINT seen_only_is_a_lead CHECK (official_url_status <> 'SEEN_IN_SEARCH' OR record_status = 'UNVERIFIED')
);
CREATE INDEX vault_benefit_jurisdiction ON ref.vault_benefit (jurisdiction, category);

CREATE TABLE ref.vault_rule_lead (
  lead_id         TEXT PRIMARY KEY CHECK (lead_id ~ '^gr\.[a-z0-9_]+$'),
  topic           TEXT NOT NULL,
  citation        TEXT NOT NULL,
  lead            TEXT NOT NULL,
  caveat          TEXT,
  record_status   TEXT NOT NULL CHECK (record_status IN ('UNVERIFIED','SOURCE_CHECKED','CONTESTED','SUPERSEDED','ILLUSTRATIVE','HEURISTIC')),
  registry_sha256 TEXT NOT NULL CHECK (registry_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE TABLE ref.vault_benefit_lead (
  benefit_id  TEXT NOT NULL REFERENCES ref.vault_benefit (benefit_id) ON DELETE CASCADE,
  lead_id     TEXT NOT NULL REFERENCES ref.vault_rule_lead (lead_id) ON DELETE CASCADE,
  PRIMARY KEY (benefit_id, lead_id)
);

CREATE TABLE ref.vault_caveat (
  caveat_id       TEXT PRIMARY KEY CHECK (caveat_id ~ '^[a-z0-9_]+$'),
  text            TEXT NOT NULL CHECK (length(text) BETWEEN 1 AND 600),
  registry_sha256 TEXT NOT NULL CHECK (registry_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE TABLE ref.vault_license_reciprocity (
  state                    TEXT PRIMARY KEY CHECK (state ~ '^[A-Z]{2}$'),
  teacher_full_reciprocity BOOLEAN NOT NULL,
  lawyer_ube               BOOLEAN NOT NULL,
  real_estate              TEXT NOT NULL CHECK (real_estate IN ('full','partial','none')),
  record_status            TEXT NOT NULL CHECK (record_status = 'UNVERIFIED'),
  registry_sha256          TEXT NOT NULL CHECK (registry_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE TABLE ref.vault_agent_manifest (
  agent_id                  TEXT PRIMARY KEY CHECK (agent_id ~ '^[a-z][a-z0-9_]{2,60}$'),
  name                      TEXT NOT NULL,
  plane                     SMALLINT NOT NULL CHECK (plane BETWEEN 1 AND 5),
  role                      TEXT NOT NULL,
  may_issue_determinations  BOOLEAN NOT NULL DEFAULT false CHECK (may_issue_determinations = false),
  may_pull_from_agents      BOOLEAN NOT NULL DEFAULT false,
  highest_class_held        TEXT NOT NULL CHECK (highest_class_held IN ('V0','V1','V2','V3','V4','V5')),
  registry_sha256           TEXT NOT NULL CHECK (registry_sha256 ~ '^[0-9a-f]{64}$'),
  CONSTRAINT only_the_vault_pulls CHECK (may_pull_from_agents = false OR agent_id = 'benefit_vault_agent')
);
CREATE UNIQUE INDEX vault_agent_one_puller ON ref.vault_agent_manifest ((true)) WHERE may_pull_from_agents;

CREATE TABLE ref.vault_agent_exposure (
  agent_id    TEXT NOT NULL REFERENCES ref.vault_agent_manifest (agent_id) ON DELETE CASCADE,
  fact_key    TEXT NOT NULL REFERENCES ref.vault_fact (fact_key),
  data_class  TEXT NOT NULL CHECK (data_class IN ('V0','V1','V2')),
  PRIMARY KEY (agent_id, fact_key)
);

-- An exposure must sit at the catalog's class, for a fact that may travel,
-- on an agent that is not the puller.
CREATE FUNCTION ref.vault_check_exposure() RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE f RECORD; puller BOOLEAN;
BEGIN
  SELECT data_class, pullable, session_only INTO f FROM ref.vault_fact WHERE fact_key = NEW.fact_key;
  IF NOT FOUND OR f.data_class <> NEW.data_class OR NOT f.pullable OR f.session_only THEN
    RAISE EXCEPTION 'agent % may not expose % as %', NEW.agent_id, NEW.fact_key, NEW.data_class
      USING ERRCODE = '23514';
  END IF;
  SELECT may_pull_from_agents INTO puller FROM ref.vault_agent_manifest WHERE agent_id = NEW.agent_id;
  IF puller THEN
    RAISE EXCEPTION 'the pulling agent exposes nothing' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER vault_agent_exposure_check BEFORE INSERT OR UPDATE ON ref.vault_agent_exposure
  FOR EACH ROW EXECUTE FUNCTION ref.vault_check_exposure();

REVOKE ALL ON ref.vault_registry_meta, ref.vault_jurisdiction, ref.vault_source, ref.vault_fact, ref.vault_benefit,
              ref.vault_rule_lead, ref.vault_benefit_lead, ref.vault_caveat, ref.vault_license_reciprocity,
              ref.vault_agent_manifest, ref.vault_agent_exposure FROM PUBLIC;
GRANT SELECT ON ref.vault_registry_meta, ref.vault_jurisdiction, ref.vault_source, ref.vault_fact, ref.vault_benefit,
                ref.vault_rule_lead, ref.vault_benefit_lead, ref.vault_caveat, ref.vault_license_reciprocity,
                ref.vault_agent_manifest, ref.vault_agent_exposure TO vetbuddy_app;

-- ── tenant tables ─────────────────────────────────────────────────────────

-- Pull grants (Mode B account grants; Mode A session grants never reach the
-- database). Revoked, never deleted by the app; vb_delete_account removes them.
CREATE TABLE public.vault_pull_grant (
  grant_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES public.tenant (tenant_id),
  grantee       TEXT NOT NULL DEFAULT 'benefit_vault_agent' CHECK (grantee = 'benefit_vault_agent'),
  source_agent  TEXT NOT NULL REFERENCES ref.vault_agent_manifest (agent_id),
  fact_keys     TEXT[] NOT NULL CHECK (cardinality(fact_keys) BETWEEN 1 AND 40),
  purpose       TEXT NOT NULL CHECK (purpose = 'benefit_matching'),
  mode          TEXT NOT NULL CHECK (mode = 'B'),
  granted_at    TIMESTAMPTZ NOT NULL,
  expires_at    TIMESTAMPTZ NOT NULL,
  revoked_at    TIMESTAMPTZ,
  CONSTRAINT grant_window CHECK (expires_at > granted_at AND expires_at <= granted_at + INTERVAL '90 days'),
  CONSTRAINT revoked_after_granted CHECK (revoked_at IS NULL OR revoked_at >= granted_at),
  CONSTRAINT not_from_the_vault CHECK (source_agent <> 'benefit_vault_agent')
);
CREATE INDEX vault_pull_grant_lookup ON public.vault_pull_grant (tenant_id, source_agent, purpose);

CREATE FUNCTION public.vault_grant_guard() RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE k TEXT; c TEXT;
BEGIN
  IF TG_OP = 'INSERT' THEN
    FOREACH k IN ARRAY NEW.fact_keys LOOP
      SELECT e.data_class INTO c FROM ref.vault_agent_exposure e
       WHERE e.agent_id = NEW.source_agent AND e.fact_key = k;
      IF c IS NULL THEN
        RAISE EXCEPTION '% does not expose %', NEW.source_agent, k USING ERRCODE = '23514';
      END IF;
      IF c NOT IN ('V0','V1','V2') THEN
        RAISE EXCEPTION '% is above the Mode B ceiling', k USING ERRCODE = '23514';
      END IF;
    END LOOP;
    NEW.fact_keys := ARRAY(SELECT DISTINCT u.fact_key COLLATE "C" FROM unnest(NEW.fact_keys) AS u(fact_key) ORDER BY 1);
    RETURN NEW;
  END IF;
  -- UPDATE: only revoking, once.
  IF NEW.grant_id <> OLD.grant_id OR NEW.tenant_id <> OLD.tenant_id OR NEW.grantee <> OLD.grantee
     OR NEW.source_agent <> OLD.source_agent OR NEW.fact_keys <> OLD.fact_keys OR NEW.purpose <> OLD.purpose
     OR NEW.mode <> OLD.mode OR NEW.granted_at <> OLD.granted_at OR NEW.expires_at <> OLD.expires_at THEN
    RAISE EXCEPTION 'a grant can only be revoked' USING ERRCODE = '23514';
  END IF;
  IF OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at THEN
    RAISE EXCEPTION 'a revoked grant stays revoked' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER vault_pull_grant_guard BEFORE INSERT OR UPDATE ON public.vault_pull_grant
  FOR EACH ROW EXECUTE FUNCTION public.vault_grant_guard();

ALTER TABLE public.vault_pull_grant ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vault_pull_grant FORCE ROW LEVEL SECURITY;
CREATE POLICY vault_pull_grant_tenant ON public.vault_pull_grant
  USING (tenant_id = public.vb_current_tenant()) WITH CHECK (tenant_id = public.vb_current_tenant());
REVOKE ALL ON public.vault_pull_grant FROM PUBLIC;
GRANT SELECT, INSERT ON public.vault_pull_grant TO vetbuddy_app;
GRANT UPDATE (revoked_at) ON public.vault_pull_grant TO vetbuddy_app;

-- The pull ledger: append-only, hash-chained per tenant, keys never values.
-- The insert trigger assigns seq, prev_hash and row_hash, so the app cannot
-- forge a chain; governance/ledger.py verifies it with the same text:
--   prev_hash|seq|tenant_id|occurred_at|event|requester|source_agent|purpose|keys|grant_id|packet_id|reason
CREATE TABLE public.vault_pull_ledger (
  tenant_id     UUID NOT NULL REFERENCES public.tenant (tenant_id),
  seq           BIGINT NOT NULL,
  occurred_at   TIMESTAMPTZ NOT NULL,
  event         TEXT NOT NULL CHECK (event IN ('PULL_ALLOWED','PULL_DENIED','GRANT_CREATED','GRANT_REVOKED')),
  requester     TEXT NOT NULL CHECK (requester ~ '^[a-z0-9_.:-]+$'),
  source_agent  TEXT NOT NULL CHECK (source_agent ~ '^[a-z0-9_.:-]+$'),
  purpose       TEXT NOT NULL CHECK (purpose ~ '^[a-z0-9_.:-]+$'),
  fact_keys     TEXT[] NOT NULL DEFAULT '{}'
                CHECK (array_to_string(fact_keys, ',') ~ '^([a-z][a-z_]*(,[a-z][a-z_]*)*)?$'),
  grant_id      TEXT NOT NULL DEFAULT '' CHECK (grant_id ~ '^[a-z0-9_.:-]*$'),
  packet_id     TEXT NOT NULL DEFAULT '' CHECK (packet_id ~ '^[a-z0-9_.:-]*$'),
  reason        TEXT NOT NULL CHECK (reason IN ('ALLOWED','REQUESTER_NOT_PERMITTED','NO_MANIFEST','NOT_EXPOSED',
                  'CLASS_NEVER_PULLABLE','CLASS_ABOVE_MODE_CEILING','NO_ACTIVE_GRANT','GRANT_EXPIRED','GRANT_REVOKED',
                  'KEY_NOT_GRANTED','PURPOSE_NOT_ALLOWED','NOT_MINIMUM_NECESSARY','SOURCE_UNAVAILABLE',
                  'MODE_C_UNREACHABLE','DURATION_NOT_ALLOWED')),
  prev_hash     TEXT NOT NULL CHECK (prev_hash ~ '^[0-9a-f]{64}$'),
  row_hash      TEXT NOT NULL CHECK (row_hash ~ '^[0-9a-f]{64}$'),
  PRIMARY KEY (tenant_id, seq),
  CONSTRAINT reason_fits_event CHECK ((event = 'PULL_DENIED') = (reason <> 'ALLOWED'))
);

CREATE FUNCTION public.vault_ledger_chain() RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE last RECORD;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('vetbuddy.vault_pull_ledger:' || NEW.tenant_id::text, 0));
  SELECT l.seq, l.row_hash INTO last FROM public.vault_pull_ledger l
   WHERE l.tenant_id = NEW.tenant_id ORDER BY l.seq DESC LIMIT 1;
  NEW.seq := COALESCE(last.seq, 0) + 1;
  NEW.prev_hash := COALESCE(last.row_hash, repeat('0', 64));
  NEW.fact_keys := ARRAY(SELECT DISTINCT u.fact_key COLLATE "C" FROM unnest(NEW.fact_keys) AS u(fact_key) ORDER BY 1);
  NEW.row_hash := encode(digest(concat_ws('|',
      NEW.prev_hash, NEW.seq::text, NEW.tenant_id::text,
      to_char(NEW.occurred_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
      NEW.event, NEW.requester, NEW.source_agent, NEW.purpose, array_to_string(NEW.fact_keys, ','),
      NEW.grant_id, NEW.packet_id, NEW.reason), 'sha256'), 'hex');
  RETURN NEW;
END $$;
CREATE TRIGGER vault_pull_ledger_chain BEFORE INSERT ON public.vault_pull_ledger
  FOR EACH ROW EXECUTE FUNCTION public.vault_ledger_chain();

-- Append-only for everyone, except the owning tenant's purge (the 0013 rule):
-- the purge setting names this tenant and the deleting role is the purger.
CREATE FUNCTION public.vault_ledger_append_only() RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE purge_tenant TEXT := current_setting('vetbuddy.purge_tenant', true);
BEGIN
  IF TG_OP = 'DELETE' AND purge_tenant IS NOT NULL AND purge_tenant <> ''
     AND OLD.tenant_id::text = purge_tenant
     AND current_user = 'vetbuddy_purger' THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'vault_pull_ledger is append-only' USING ERRCODE = '42501';
END $$;
CREATE TRIGGER vault_pull_ledger_append_only BEFORE UPDATE OR DELETE ON public.vault_pull_ledger
  FOR EACH ROW EXECUTE FUNCTION public.vault_ledger_append_only();

CREATE FUNCTION public.vault_ledger_no_truncate() RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  RAISE EXCEPTION 'vault_pull_ledger cannot be truncated' USING ERRCODE = '42501';
END $$;
CREATE TRIGGER vault_pull_ledger_no_truncate BEFORE TRUNCATE ON public.vault_pull_ledger
  FOR EACH STATEMENT EXECUTE FUNCTION public.vault_ledger_no_truncate();

ALTER TABLE public.vault_pull_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vault_pull_ledger FORCE ROW LEVEL SECURITY;
CREATE POLICY vault_pull_ledger_tenant ON public.vault_pull_ledger
  USING (tenant_id = public.vb_current_tenant()) WITH CHECK (tenant_id = public.vb_current_tenant());
REVOKE ALL ON public.vault_pull_ledger FROM PUBLIC;
GRANT SELECT, INSERT ON public.vault_pull_ledger TO vetbuddy_app;

-- Saved benefits: the person's own list. No free text is stored. The record
-- id is not a foreign key, so retiring a record never deletes a person's row;
-- the API shows such rows as retired.
CREATE TABLE public.vault_saved_benefit (
  saved_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL REFERENCES public.tenant (tenant_id),
  benefit_id            TEXT NOT NULL CHECK (benefit_id ~ '^[a-z]{2}\.[a-z0-9-]{1,80}$'),
  status                TEXT NOT NULL CHECK (status IN ('INTERESTED','GATHERING_DOCUMENTS','APPLIED_ON_MY_OWN','NOT_FOR_ME')),
  content_hash_at_save  TEXT NOT NULL CHECK (content_hash_at_save ~ '^[0-9a-f]{64}$'),
  saved_at              TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  UNIQUE (tenant_id, benefit_id)
);

CREATE FUNCTION public.vault_saved_guard() RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NOT EXISTS (SELECT 1 FROM ref.vault_benefit b WHERE b.benefit_id = NEW.benefit_id) THEN
      RAISE EXCEPTION 'no such benefit %', NEW.benefit_id USING ERRCODE = '23503';
    END IF;
    RETURN NEW;
  END IF;
  IF NEW.saved_id <> OLD.saved_id OR NEW.tenant_id <> OLD.tenant_id OR NEW.benefit_id <> OLD.benefit_id
     OR NEW.content_hash_at_save <> OLD.content_hash_at_save OR NEW.saved_at <> OLD.saved_at THEN
    RAISE EXCEPTION 'only the status of a saved benefit can change' USING ERRCODE = '23514';
  END IF;
  NEW.updated_at := clock_timestamp();
  RETURN NEW;
END $$;
CREATE TRIGGER vault_saved_benefit_guard BEFORE INSERT OR UPDATE ON public.vault_saved_benefit
  FOR EACH ROW EXECUTE FUNCTION public.vault_saved_guard();

ALTER TABLE public.vault_saved_benefit ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vault_saved_benefit FORCE ROW LEVEL SECURITY;
CREATE POLICY vault_saved_benefit_tenant ON public.vault_saved_benefit
  USING (tenant_id = public.vb_current_tenant()) WITH CHECK (tenant_id = public.vb_current_tenant());
REVOKE ALL ON public.vault_saved_benefit FROM PUBLIC;
GRANT SELECT, INSERT ON public.vault_saved_benefit TO vetbuddy_app;
GRANT UPDATE (status, updated_at) ON public.vault_saved_benefit TO vetbuddy_app;

-- The app holds no DELETE grant. A person removes a saved benefit, or a grant
-- that is already revoked or expired, through this function, scoped to the
-- caller's tenant. The ledger is never discarded; account deletion
-- (vb_delete_account) removes it with everything else. Like the 0013
-- functions it runs as vetbuddy_purger (owner set below), which is subject to
-- forced RLS, so the tenant scope is enforced twice: the WHERE clause and the
-- policy.
CREATE FUNCTION public.vb_vault_discard(p_kind TEXT, p_id UUID) RETURNS BOOLEAN
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public, pg_temp AS $fn$
DECLARE
  current_tenant UUID := public.vb_current_tenant();
  removed INTEGER;
BEGIN
  IF current_tenant IS NULL THEN
    RAISE EXCEPTION 'no tenant in this session' USING ERRCODE = '42501';
  END IF;
  CASE p_kind
    WHEN 'saved_benefit' THEN
      DELETE FROM public.vault_saved_benefit WHERE saved_id = p_id AND tenant_id = current_tenant;
    WHEN 'grant' THEN
      DELETE FROM public.vault_pull_grant
       WHERE grant_id = p_id AND tenant_id = current_tenant
         AND (revoked_at IS NOT NULL OR expires_at <= clock_timestamp());
    ELSE
      RAISE EXCEPTION 'unknown kind %', p_kind USING ERRCODE = '22023';
  END CASE;
  GET DIAGNOSTICS removed = ROW_COUNT;
  RETURN removed > 0;
END
$fn$;
REVOKE ALL ON FUNCTION public.vb_vault_discard(TEXT, UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.vb_vault_discard(TEXT, UUID) TO vetbuddy_app;

-- Account deletion reaches the vault tables through vetbuddy_purger (0013).
GRANT SELECT, DELETE ON public.vault_pull_grant, public.vault_pull_ledger, public.vault_saved_benefit
  TO vetbuddy_purger;
ALTER FUNCTION public.vb_vault_discard(TEXT, UUID) OWNER TO vetbuddy_purger;

-- ── postconditions ────────────────────────────────────────────────────────
DO $postcheck$
DECLARE
  bad TEXT;
BEGIN
  -- The 0012 rule for every public vault table.
  SELECT string_agg(c.relname, ', ' ORDER BY c.relname) INTO bad
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname LIKE 'vault\_%'
     AND NOT (
          c.relrowsecurity AND c.relforcerowsecurity
      AND EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid = c.oid)
      AND EXISTS (SELECT 1 FROM pg_attribute a
                   WHERE a.attrelid = c.oid AND a.attname = 'tenant_id' AND a.attnotnull AND NOT a.attisdropped)
      AND EXISTS (SELECT 1 FROM pg_constraint k
                   WHERE k.conrelid = c.oid AND k.contype = 'f' AND k.confrelid = 'public.tenant'::regclass)
      AND NOT has_table_privilege('vetbuddy_app', c.oid, 'DELETE')
      AND NOT has_table_privilege('vetbuddy_app', c.oid, 'TRUNCATE'));
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'tenant table rule violated by: %', bad;
  END IF;
  -- Account deletion must reach every tenant table (0013 fails closed otherwise).
  SELECT string_agg(c.table_name::text, ', ' ORDER BY c.table_name) INTO bad
    FROM information_schema.columns c
    JOIN information_schema.tables it ON it.table_schema = c.table_schema AND it.table_name = c.table_name
   WHERE c.table_schema = 'public' AND c.column_name = 'tenant_id' AND it.table_type = 'BASE TABLE'
     AND NOT (has_table_privilege('vetbuddy_purger', format('public.%I', c.table_name), 'DELETE')
          AND has_table_privilege('vetbuddy_purger', format('public.%I', c.table_name), 'SELECT'));
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'account deletion cannot reach: %', bad;
  END IF;
  -- The ledger is append-only for the app: no UPDATE privilege on any column.
  IF has_any_column_privilege('vetbuddy_app', 'public.vault_pull_ledger', 'UPDATE') THEN
    RAISE EXCEPTION 'vault_pull_ledger must not be updatable by vetbuddy_app';
  END IF;
  -- Reference tables are read-only for the app.
  SELECT string_agg(c.relname, ', ' ORDER BY c.relname) INTO bad
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'ref' AND c.relkind = 'r' AND c.relname LIKE 'vault\_%'
     AND (has_table_privilege('vetbuddy_app', c.oid, 'INSERT') OR has_table_privilege('vetbuddy_app', c.oid, 'UPDATE')
          OR has_table_privilege('vetbuddy_app', c.oid, 'DELETE') OR has_table_privilege('vetbuddy_app', c.oid, 'TRUNCATE'));
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'reference tables writable by vetbuddy_app: %', bad;
  END IF;
END
$postcheck$;
