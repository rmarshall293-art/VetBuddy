-- Plane 2: Work OS (v4.0 §15, §16, §40). Mission -> Case (lane) -> Task/Deadline.
CREATE TABLE installation (
    installation_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL REFERENCES tenant(tenant_id),
    jurisdiction_id  UUID REFERENCES jurisdiction(jurisdiction_id),
    name             TEXT NOT NULL,
    branch           TEXT,
    country          TEXT NOT NULL DEFAULT 'US',
    latitude         NUMERIC(9,6),
    longitude        NUMERIC(9,6),
    services         TEXT[],            -- TAP, family readiness, legal, behavioral health, etc.
    overseas         BOOLEAN NOT NULL DEFAULT false,
    last_verified    DATE
);

-- Transition lifecycle clock (v4.0 §4): stage is first-class, not a note.
CREATE TABLE transition_context (
    transition_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id           UUID NOT NULL REFERENCES person_profile(person_id),
    track               TEXT NOT NULL CHECK (track IN ('ets_eas','retirement','medical_separation',
                            'guard_reserve','pcs','overseas_return','student','employment',
                            'federal_employment','apprenticeship','entrepreneurship','spouse_family','re_entry')),
    stage               TEXT NOT NULL,   -- e.g. T-24..T-12, T-180..T-90, Day0..30, Year1..2, Ongoing
    separation_date     DATE,
    current_installation_id     UUID REFERENCES installation(installation_id),
    destination_installation_id UUID REFERENCES installation(installation_id),
    current_jurisdiction_id     UUID REFERENCES jurisdiction(jurisdiction_id),
    destination_jurisdiction_id UUID REFERENCES jurisdiction(jurisdiction_id),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE mission (
    mission_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id      UUID NOT NULL REFERENCES person_profile(person_id),
    title          TEXT NOT NULL,
    primary_lane   TEXT NOT NULL,
    urgency        TEXT NOT NULL DEFAULT '30_days' CHECK (urgency IN ('immediate','7_days','30_days','90_days','long_term','info_only')),
    status         TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','paused','completed','closed')),
    router_policy_version TEXT,        -- deterministic Mission Router output is versioned (v4.0 §18)
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE crm_case (
    case_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES tenant(tenant_id),   -- closes the "no tenant_id" defect
    mission_id     UUID NOT NULL REFERENCES mission(mission_id),
    lane           TEXT NOT NULL CHECK (lane IN ('benefits','claims_evidence','career','education','financial',
                       'healthcare_coverage','housing_stability','family_caregiver_survivor','guard_reserve',
                       'state_local','recreation_community','citizenship','other')),
    status         TEXT NOT NULL DEFAULT 'open',
    priority       SMALLINT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    owner_user_id  UUID REFERENCES app_user(user_id),
    closure_reason TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE task (
    task_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES tenant(tenant_id),
    case_id        UUID NOT NULL REFERENCES crm_case(case_id),
    title          TEXT NOT NULL,
    description    TEXT,
    status         TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo','in_progress','blocked','done','cancelled')),
    priority       SMALLINT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    due_date       DATE,
    assigned_user_id  UUID REFERENCES app_user(user_id),
    assigned_agent_id TEXT REFERENCES agent_manifest(agent_id),
    ai_generated   BOOLEAN NOT NULL DEFAULT false,
    depends_on     UUID[] NOT NULL DEFAULT '{}',
    source_id      UUID,               -- source_record the task is based on (0007)
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE deadline (
    deadline_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES tenant(tenant_id),
    case_id        UUID NOT NULL REFERENCES crm_case(case_id),
    kind           TEXT NOT NULL,      -- claim, appeal, education, application, renewal, benefit_expiration
    due_date       DATE NOT NULL,
    benefit_id     UUID REFERENCES benefit(benefit_id),
    notify_priority TEXT NOT NULL DEFAULT 'important' CHECK (notify_priority IN ('critical','important','recommended','informational'))
);

CREATE TABLE appointment (
    appointment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES tenant(tenant_id),
    case_id        UUID NOT NULL REFERENCES crm_case(case_id),
    resource_id    UUID REFERENCES resource(resource_id),
    starts_at      TIMESTAMPTZ NOT NULL,
    notes          TEXT
);

DO $$ DECLARE t TEXT; BEGIN
  FOREACH t IN ARRAY ARRAY['installation','transition_context','mission','crm_case','task','deadline','appointment'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('CREATE POLICY tenant_isolation_%1$s ON %1$I USING (tenant_id = current_setting(''vetbuddy.tenant_id'')::uuid)', t);
  END LOOP;
END $$;
