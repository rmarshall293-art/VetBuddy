-- Reused pattern from the real, tested prototype (agent_boundary.py /
-- context_fabric.py). This is the contract every agent you add must satisfy.

CREATE TABLE agent_manifest (
    agent_id                 TEXT PRIMARY KEY,
    version                  TEXT NOT NULL,
    mission                  TEXT NOT NULL,
    status                   TEXT NOT NULL DEFAULT 'NOT_IMPLEMENTED'
                             CHECK (status IN ('NOT_IMPLEMENTED','DRAFT','SIMULATION','PRODUCTION','RETIRED')),
    readable_data_classes    TEXT[] NOT NULL DEFAULT '{}',
    writable_data_classes    TEXT[] NOT NULL DEFAULT '{}',
    prohibited_data_classes  TEXT[] NOT NULL DEFAULT '{}',
    allowed_purposes         TEXT[] NOT NULL DEFAULT '{}',
    approved_tools           TEXT[] NOT NULL DEFAULT '{}',
    confidence_threshold     NUMERIC(3,2) DEFAULT 0.70,
    human_review_threshold   NUMERIC(3,2) DEFAULT 0.50,
    configuration_hash       TEXT NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- NO MANIFEST, NO ACCESS: application code must reject any agent call
-- where agent_id has no row here, full stop — this is not optional.

CREATE TABLE context_packet (
    packet_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id              UUID NOT NULL REFERENCES tenant(tenant_id),
    mission_id             UUID,
    case_id                UUID,
    originating_agent      TEXT NOT NULL REFERENCES agent_manifest(agent_id),
    destination_agent      TEXT NOT NULL REFERENCES agent_manifest(agent_id),
    purpose_of_use         TEXT NOT NULL,
    approved_fields        TEXT[] NOT NULL,
    redacted_fields        TEXT[] NOT NULL DEFAULT '{}',
    consent_reference      UUID REFERENCES consent_record(consent_id),
    expires_at             TIMESTAMPTZ NOT NULL,
    integrity_hash         TEXT NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE approval (
    approval_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id              UUID NOT NULL REFERENCES tenant(tenant_id),
    submitted_by_user_id   UUID NOT NULL REFERENCES app_user(user_id),
    decided_by_user_id     UUID REFERENCES app_user(user_id),
    -- Fixes the pinned self-approval defect at the schema level.
    CONSTRAINT no_self_approval CHECK (decided_by_user_id IS NULL OR decided_by_user_id <> submitted_by_user_id),
    subject_type           TEXT NOT NULL,
    subject_id             UUID NOT NULL,
    risk_level             SMALLINT NOT NULL CHECK (risk_level BETWEEN 0 AND 5),
    status                 TEXT NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending','approved','rejected','expired')),
    -- Fixes the pinned in-memory-approval-state defect: this table IS the
    -- durable store, so approvals survive worker restarts and load balancing.
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at             TIMESTAMPTZ,
    expires_at             TIMESTAMPTZ NOT NULL
);

ALTER TABLE context_packet ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_packet ON context_packet USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);
CREATE POLICY tenant_isolation_approval ON approval USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);

-- Seed manifests: existing verified agents as PRODUCTION, new ones as
-- NOT_IMPLEMENTED placeholders you fill in per docs/ARCHITECTURE.md §3.
INSERT INTO agent_manifest (agent_id, version, mission, status, configuration_hash) VALUES
 ('intake_agent', '1.0', 'Progressive onboarding and needs triage', 'PRODUCTION', 'seed'),
 ('federal_benefits_agent', '1.0', 'Explain federal benefit matches with citations', 'PRODUCTION', 'seed'),
 ('alabama_state_benefits_agent', '1.0', 'Explain Alabama-verified state benefit matches', 'PRODUCTION', 'seed'),
 ('document_agent', '1.0', 'Document intake and classification', 'PRODUCTION', 'seed'),
 ('career_mos_agent', '0.1', 'MOS-to-civilian occupation translation', 'NOT_IMPLEMENTED', 'seed'),
 ('resume_builder_agent', '0.1', 'DD-214-based resume drafting', 'NOT_IMPLEMENTED', 'seed'),
 ('job_matching_agent', '0.1', 'Score job matches against career profile', 'NOT_IMPLEMENTED', 'seed'),
 ('guard_reserve_agent', '0.1', 'Guard/Reserve status-aware benefit routing', 'NOT_IMPLEMENTED', 'seed'),
 ('women_veterans_agent', '0.1', 'Trauma-informed women-veteran resource routing', 'NOT_IMPLEMENTED', 'seed'),
 ('installation_navigator_agent', '0.1', 'Base/installation resource lookup', 'NOT_IMPLEMENTED', 'seed');
