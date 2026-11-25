-- 0021 — Guard & Reserve role of Benefits Intelligence (ADR 0011).
--
-- The platform manifest row seeded by 0005 as a NOT_IMPLEMENTED placeholder
-- ("guard_reserve_agent", "Guard/Reserve status-aware benefit routing") is
-- realigned with the v8 roster (migration 0015): the agent is the Guard/Reserve
-- role of benefits_intelligence_agent, implemented and tested, DRAFT until G1
-- and G17 close. It reads only what the vault holds for a request (V1 and V2
-- facts plus the person's own V1 Guard & Reserve answers), never pulls, never
-- writes, never decides.
--
-- The vault-side manifest (ref.vault_agent_manifest) comes from the generated
-- seed (config/benefit_vault_policy.yaml); the database pins there already
-- refuse any second puller or any decision.
--
-- configuration_hash is the SHA-256 of the canonical JSON of this agent's entry
-- in backend/app/agents/registry.json (keys sorted, separators "," and ":",
-- UTF-8); a test fails when the two drift.

UPDATE agent_manifest SET
  version                 = '1.0.0',
  mission                 = 'Show National Guard, Reserve and AGR members the Benefit Vault''s records from their component, duty status and the legal authority on their orders (Title 10/32/SAD), never from component alone. Classify duty as the Sentinel dataset does; never decide.',
  status                  = 'DRAFT',
  readable_data_classes   = ARRAY['vault.facts:V1', 'vault.facts:V2', 'guard_reserve.answers:V1'],
  writable_data_classes   = ARRAY[]::text[],
  prohibited_data_classes = ARRAY['V3', 'V4', 'V5', 'health', 'claims_evidence', 'financial', 'immigration_status'],
  allowed_purposes        = ARRAY['benefit_matching'],
  approved_tools          = ARRAY['vault_matcher', 'sentinel_duty_classifier', 'sentinel_rule_lead_checks'],
  configuration_hash      = '3a27b727620ccd0a101f21e3f8d41210cbcc5d1109038aefa5570745e4f59a45'
WHERE agent_id = 'guard_reserve_agent';

DO $postcheck$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM agent_manifest WHERE agent_id = 'guard_reserve_agent' AND status = 'DRAFT'
                    AND writable_data_classes = '{}' AND 'V4' = ANY (prohibited_data_classes)) THEN
    RAISE EXCEPTION 'guard_reserve_agent manifest was not realigned';
  END IF;
END
$postcheck$;
