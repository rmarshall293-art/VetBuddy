-- 0001 Foundation: schema, the non-owner application role, tenant context helpers.
--
-- The API connects as a LOGIN role that is a member of vetbuddy_app. That role
-- owns nothing, has no BYPASSRLS, and gets per-table grants in later migrations.
-- Every table forces RLS so the schema owner obeys policies too.
--
-- vetbuddy_definer owns the few SECURITY DEFINER functions (identity
-- resolution, audit chaining). It cannot log in, and its policies are written
-- per table, so a definer function can reach only what its policy names.

CREATE SCHEMA IF NOT EXISTS vb;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vetbuddy_app') THEN
    CREATE ROLE vetbuddy_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vetbuddy_definer') THEN
    CREATE ROLE vetbuddy_definer NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
  END IF;
  -- The migrating role must be able to hand function ownership to the definer role.
  EXECUTE format('GRANT vetbuddy_definer TO %I', current_user);
END
$$;

REVOKE ALL ON SCHEMA vb FROM PUBLIC;
GRANT USAGE ON SCHEMA vb TO vetbuddy_app, vetbuddy_definer;

-- Request context is set per transaction with set_config(..., true) by the API.
-- Unset or empty -> NULL -> every tenant policy matches zero rows (fail closed, I10).
CREATE OR REPLACE FUNCTION vb.current_tenant() RETURNS uuid
  LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('app.tenant_id', true), '')::uuid $$;

CREATE OR REPLACE FUNCTION vb.current_user_id() RETURNS uuid
  LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('app.user_id', true), '')::uuid $$;

GRANT EXECUTE ON FUNCTION vb.current_tenant(), vb.current_user_id() TO vetbuddy_app, vetbuddy_definer;
