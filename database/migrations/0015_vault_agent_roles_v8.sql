-- 0015 — Benefit Vault helper names follow the v8 role roster (owner decision VD06, 2026-10-29; ADR 0006).
--
--   benefit_vault_agent     -> benefits_intelligence_agent  (v8 "Benefits Intelligence": Federal Benefits,
--                                                             State & Territory and Guard/Reserve roles)
--   claims_navigator_agent  -> claims_navigation_agent      (v8 "Claims Navigation")
--   crisis_support_agent    -> removed. Crisis help is a Tier 0 rule, not an agent: v8 says safety
--                              resources bypass every gate. The vault's CrisisGate (guards.py) and the
--                              crisis floor (config/crisis_floor.yaml) are unchanged.
--
-- 0014 is applied and immutable, so this migration moves its pins forward. It works on a fresh database
-- (reference tables still empty; the seed runs after every migration) and on one that already holds the
-- 0014 seed and account grants. Pull-ledger rows keep the name they were written with: the ledger is
-- hash-chained history and is never rewritten (its requester column takes any id).

-- Reference manifests: drop the pin, rename or remove the three rows, pin the new id.
ALTER TABLE ref.vault_agent_manifest DROP CONSTRAINT only_the_vault_pulls;
UPDATE ref.vault_agent_manifest SET agent_id = 'benefits_intelligence_agent' WHERE agent_id = 'benefit_vault_agent';
UPDATE ref.vault_agent_manifest SET agent_id = 'claims_navigation_agent' WHERE agent_id = 'claims_navigator_agent';
DELETE FROM ref.vault_agent_manifest WHERE agent_id = 'crisis_support_agent';
ALTER TABLE ref.vault_agent_manifest ADD CONSTRAINT only_the_vault_pulls
  CHECK (may_pull_from_agents = false OR agent_id = 'benefits_intelligence_agent');

-- Account grants: the grantee is always the vault. Its guard trigger allows only revoking, so it is
-- paused for this one owner-run rename inside the migration's transaction.
ALTER TABLE public.vault_pull_grant DROP CONSTRAINT vault_pull_grant_grantee_check;
ALTER TABLE public.vault_pull_grant DROP CONSTRAINT not_from_the_vault;
ALTER TABLE public.vault_pull_grant DISABLE TRIGGER vault_pull_grant_guard;
UPDATE public.vault_pull_grant SET grantee = 'benefits_intelligence_agent' WHERE grantee = 'benefit_vault_agent';
ALTER TABLE public.vault_pull_grant ENABLE TRIGGER vault_pull_grant_guard;
ALTER TABLE public.vault_pull_grant ALTER COLUMN grantee SET DEFAULT 'benefits_intelligence_agent';
ALTER TABLE public.vault_pull_grant ADD CONSTRAINT vault_pull_grant_grantee_check
  CHECK (grantee = 'benefits_intelligence_agent');
ALTER TABLE public.vault_pull_grant ADD CONSTRAINT not_from_the_vault
  CHECK (source_agent <> 'benefits_intelligence_agent');

DO $postcheck$
BEGIN
  IF EXISTS (SELECT 1 FROM ref.vault_agent_manifest
              WHERE agent_id IN ('benefit_vault_agent', 'claims_navigator_agent', 'crisis_support_agent')) THEN
    RAISE EXCEPTION 'old vault helper names remain in ref.vault_agent_manifest';
  END IF;
  IF EXISTS (SELECT 1 FROM public.vault_pull_grant WHERE grantee <> 'benefits_intelligence_agent') THEN
    RAISE EXCEPTION 'a grant names a grantee other than benefits_intelligence_agent';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'vault_pull_grant_guard' AND tgenabled = 'O') THEN
    RAISE EXCEPTION 'vault_pull_grant_guard is not enabled';
  END IF;
END
$postcheck$;
