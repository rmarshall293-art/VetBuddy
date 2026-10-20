-- 0006 RLS guard (closes C-06: RLS enabled with no policy on some tables).
--
-- vb.rls_gaps() lists every table in schema vb that is missing forced RLS or
-- has no policy at all. The migration fails if the list is non-empty, and
-- tests/test_schema_guard.py calls it again after all migrations. Any later
-- migration that adds a table must add its policies in the same file.

CREATE OR REPLACE FUNCTION vb.rls_gaps() RETURNS TABLE (table_name text, problem text)
  LANGUAGE sql STABLE AS $$
  SELECT c.relname::text,
         CASE WHEN NOT c.relrowsecurity THEN 'rls not enabled'
              WHEN NOT c.relforcerowsecurity THEN 'rls not forced'
              ELSE 'no policy' END
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'vb' AND c.relkind = 'r'
     AND c.relname <> 'schema_migrations'
     AND (NOT c.relrowsecurity OR NOT c.relforcerowsecurity
          OR NOT EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid = c.oid))
$$;

DO $$
DECLARE gaps text;
BEGIN
  SELECT string_agg(table_name || ': ' || problem, ', ') INTO gaps FROM vb.rls_gaps();
  IF gaps IS NOT NULL THEN
    RAISE EXCEPTION 'RLS gaps: %', gaps;
  END IF;
END
$$;
