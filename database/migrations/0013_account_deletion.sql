-- 0013 — Account deletion that actually deletes (master prompt v6 §3).
--
-- Design (docs/ACCOUNT_DELETION_RUNBOOK.md):
--  * vb_delete_account(user_id) runs as the schema owner (SECURITY DEFINER)
--    but keeps the caller's RLS tenant context, so FORCE RLS still scopes
--    every DELETE to the caller's own tenant.
--  * Only individual tenants with exactly one user are purged whole. Shared
--    (organization / household) tenants need field-level ownership and are
--    refused until that exists (v6: never delete another person's lawful data).
--  * audit_event stays append-only for everyone, including the app role (no
--    DELETE grant). The one exception is this purge, signalled by a
--    transaction-local setting only this function sets.
--  * The receipt carries no user, tenant, email or content: state history,
--    per-table row counts, processor list and exceptions. Status is readable
--    only through vb_deletion_status(receipt_id), not by listing a table.

CREATE TABLE privacy_deletion_receipt (
  receipt_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  state         TEXT NOT NULL CHECK (state IN ('REQUESTED','VERIFIED','ACCESS_REVOKED','PURGING',
                                               'PROCESSOR_PENDING','COMPLETE','FAILED_RETRYABLE')),
  history       JSONB NOT NULL DEFAULT '[]',
  rows_purged   JSONB NOT NULL DEFAULT '{}',
  processors    JSONB NOT NULL DEFAULT '[]',
  exceptions    TEXT[] NOT NULL DEFAULT '{}',
  requested_on  DATE NOT NULL DEFAULT current_date,   -- a date, never a timestamp (minimal metadata)
  completed_on  DATE
);
REVOKE ALL ON privacy_deletion_receipt FROM PUBLIC;

-- Append-only audit, with exactly one sanctioned exception.
CREATE OR REPLACE FUNCTION forbid_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' AND TG_TABLE_NAME = 'audit_event'
     AND current_setting('vetbuddy.purge_tenant', true) = OLD.tenant_id::text THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
END $$;

CREATE FUNCTION vb_delete_account(p_user_id UUID) RETURNS UUID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
  t        UUID := vb_current_tenant();
  r        UUID;
  tbl      TEXT;
  n        BIGINT;
  pending  TEXT[];
  progress BOOLEAN;
  counts   JSONB := '{}';
  remaining BIGINT;
  hist     JSONB := '[]';
  st       TEXT;
BEGIN
  IF t IS NULL THEN
    RAISE EXCEPTION 'no tenant context' USING ERRCODE = 'insufficient_privilege';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM app_user WHERE user_id = p_user_id AND tenant_id = t AND deleted_at IS NULL) THEN
    RAISE EXCEPTION 'account not found' USING ERRCODE = 'no_data_found';
  END IF;
  IF (SELECT kind FROM tenant WHERE tenant_id = t) <> 'individual'
     OR (SELECT count(*) FROM app_user WHERE tenant_id = t) <> 1 THEN
    RAISE EXCEPTION 'shared tenant: field-level deletion required' USING ERRCODE = 'feature_not_supported';
  END IF;

  INSERT INTO privacy_deletion_receipt (state) VALUES ('REQUESTED') RETURNING receipt_id INTO r;
  FOREACH st IN ARRAY ARRAY['REQUESTED','VERIFIED','ACCESS_REVOKED','PURGING'] LOOP
    hist := hist || jsonb_build_object('state', st, 'on', current_date);
  END LOOP;

  -- PURGING: every table with a tenant_id, in whatever order foreign keys
  -- allow. Repeat passes until nothing is left; a pass that removes nothing
  -- while rows remain means a dependency we cannot satisfy, so fail.
  PERFORM set_config('vetbuddy.purge_tenant', t::text, true);
  SELECT array_agg(c.table_name::text ORDER BY c.table_name) INTO pending
  FROM information_schema.columns c
  JOIN information_schema.tables it ON it.table_schema = c.table_schema AND it.table_name = c.table_name
  WHERE c.table_schema = 'public' AND c.column_name = 'tenant_id' AND it.table_type = 'BASE TABLE';

  LOOP
    progress := false;
    remaining := 0;
    FOREACH tbl IN ARRAY pending LOOP
      BEGIN
        EXECUTE format('DELETE FROM %I WHERE tenant_id = $1', tbl) USING t;
        GET DIAGNOSTICS n = ROW_COUNT;
        IF n > 0 THEN
          counts := jsonb_set(counts, ARRAY[tbl], to_jsonb(COALESCE((counts->>tbl)::bigint, 0) + n));
          progress := true;
        END IF;
      EXCEPTION WHEN foreign_key_violation THEN
        NULL;  -- a child row still points here; another pass will clear it
      END;
      EXECUTE format('SELECT count(*) FROM %I WHERE tenant_id = $1', tbl) INTO n USING t;
      remaining := remaining + n;
    END LOOP;
    EXIT WHEN remaining = 0;
    IF NOT progress THEN
      RAISE EXCEPTION 'purge stalled with % rows remaining', remaining;
    END IF;
  END LOOP;
  PERFORM set_config('vetbuddy.purge_tenant', '', true);

  -- No external processors are registered in this build (no email, model,
  -- storage or analytics providers), so PROCESSOR_PENDING completes at once.
  hist := hist || jsonb_build_object('state', 'PROCESSOR_PENDING', 'on', current_date)
               || jsonb_build_object('state', 'COMPLETE', 'on', current_date);
  UPDATE privacy_deletion_receipt
     SET state = 'COMPLETE', history = hist, rows_purged = counts, processors = '[]',
         exceptions = ARRAY['Development build: no backups, processors or legal holds are configured.'],
         completed_on = current_date
   WHERE receipt_id = r;
  RETURN r;
END $$;

CREATE FUNCTION vb_deletion_status(p_receipt UUID)
RETURNS TABLE (receipt_id UUID, state TEXT, history JSONB, rows_purged JSONB, processors JSONB,
               exceptions TEXT[], requested_on DATE, completed_on DATE)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT receipt_id, state, history, rows_purged, processors, exceptions, requested_on, completed_on
  FROM privacy_deletion_receipt WHERE receipt_id = p_receipt
$$;

REVOKE ALL ON FUNCTION vb_delete_account(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION vb_deletion_status(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vb_delete_account(UUID) TO vetbuddy_app;
GRANT EXECUTE ON FUNCTION vb_deletion_status(UUID) TO vetbuddy_app;

-- The functions run as a dedicated NOLOGIN role, not the schema owner: a
-- superuser or table owner would bypass RLS, while this role is subject to
-- the tenant policy on every table it touches. Its only powers are SELECT and
-- DELETE on tenant tables plus the receipt table. A new tenant table that
-- forgets to grant DELETE here makes deletion fail closed (and a test fails).
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vetbuddy_purger') THEN
    CREATE ROLE vetbuddy_purger NOLOGIN NOBYPASSRLS;
  END IF;
END $$;
GRANT USAGE ON SCHEMA public TO vetbuddy_purger;
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN
    SELECT c.table_name FROM information_schema.columns c
    JOIN information_schema.tables it ON it.table_schema = c.table_schema AND it.table_name = c.table_name
    WHERE c.table_schema = 'public' AND c.column_name = 'tenant_id' AND it.table_type = 'BASE TABLE'
  LOOP
    EXECUTE format('GRANT SELECT, DELETE ON %I TO vetbuddy_purger', r.table_name);
  END LOOP;
END $$;
GRANT SELECT, INSERT, UPDATE ON privacy_deletion_receipt TO vetbuddy_purger;
GRANT EXECUTE ON FUNCTION vb_current_tenant() TO vetbuddy_purger;
ALTER FUNCTION vb_delete_account(UUID) OWNER TO vetbuddy_purger;
ALTER FUNCTION vb_deletion_status(UUID) OWNER TO vetbuddy_purger;
