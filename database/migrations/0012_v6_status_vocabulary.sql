-- 0012 — Implementation labels follow master prompt v6 §0 (ADR 0004).
-- 0011 is applied history and is not edited; this migration replaces its
-- CHECK and translates any rows already loaded. The reference seed is a full
-- refresh and re-inserts with the new labels from data/reference/*.json.

DO $$
DECLARE c TEXT;
BEGIN
  SELECT con.conname INTO c
  FROM pg_constraint con
  JOIN pg_class rel ON rel.oid = con.conrelid
  JOIN pg_namespace ns ON ns.oid = rel.relnamespace
  WHERE ns.nspname = 'ref' AND rel.relname = 'governance_rule' AND con.contype = 'c'
    AND pg_get_constraintdef(con.oid) LIKE '%repo_status%';
  IF c IS NULL THEN
    RAISE EXCEPTION 'expected a repo_status CHECK on ref.governance_rule';
  END IF;
  EXECUTE format('ALTER TABLE ref.governance_rule DROP CONSTRAINT %I', c);
END $$;

UPDATE ref.governance_rule SET repo_status = CASE repo_status
    WHEN 'IMPLEMENTED_VERIFIED' THEN 'IMPLEMENTED_TESTED'
    WHEN 'IMPLEMENTED_UNTESTED' THEN 'IMPLEMENTED_UNVERIFIED'
    WHEN 'NOT_PRESENT'          THEN 'PLANNED'
    WHEN 'BLOCKED_SOURCE'       THEN 'BLOCKED'
    WHEN 'DEFERRED'             THEN 'PLANNED'
    ELSE repo_status END
  WHERE repo_status IS NOT NULL;

ALTER TABLE ref.governance_rule ADD CONSTRAINT governance_rule_repo_status_v6 CHECK (
  repo_status IN ('IMPLEMENTED_TESTED','IMPLEMENTED_UNVERIFIED','PARTIAL','MOCK','PLANNED','DISABLED','BLOCKED'));
