-- Evidence layer, claims, education, closed-loop referrals, Source Registry.
CREATE TABLE source_record (          -- Data Trust Card registry (v4.0 §22)
    source_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    source_owner    TEXT NOT NULL,
    authority_tier  SMALLINT NOT NULL CHECK (authority_tier BETWEEN 1 AND 4),
    official_url    TEXT NOT NULL,
    effective_date  DATE, publication_date DATE,
    last_verified   DATE NOT NULL, next_review DATE NOT NULL,
    reviewer        TEXT,
    source_status   TEXT NOT NULL DEFAULT 'current' CHECK (source_status IN ('current','stale','changed','superseded','broken')),
    content_hash    TEXT,             -- Regulatory Patch Manager change detection (v4.0 §23)
    archived_snapshot_ref TEXT,
    version         INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE policy_version (
    policy_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    source_id       UUID NOT NULL REFERENCES source_record(source_id),
    benefit_id      UUID REFERENCES benefit(benefit_id),
    version         INTEGER NOT NULL, effective_from DATE NOT NULL, effective_to DATE,
    status          TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','human_reviewed','published','rolled_back')),
    UNIQUE (benefit_id, version)
);

CREATE TABLE document (               -- originals are immutable (v4.0 §29)
    document_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id       UUID NOT NULL REFERENCES person_profile(person_id),
    case_id         UUID REFERENCES crm_case(case_id),
    doc_type        TEXT,             -- dd214, ngb22, orders, les, transcript, va_decision ...
    classification  TEXT NOT NULL CHECK (classification IN ('V0','V1','V2','V3','V4','V5')),
    storage_key     TEXT NOT NULL,
    sha256          TEXT NOT NULL,
    malware_scan    TEXT NOT NULL DEFAULT 'pending' CHECK (malware_scan IN ('pending','clean','infected')),
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE extracted_fact (         -- provenance on every fact; conflicts are never silently deleted
    fact_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    document_id     UUID NOT NULL REFERENCES document(document_id),
    page            INTEGER, field TEXT NOT NULL, value JSONB NOT NULL,
    confidence      NUMERIC(3,2), user_corrected BOOLEAN NOT NULL DEFAULT false,
    superseded_by   UUID REFERENCES extracted_fact(fact_id)
);

CREATE TABLE claim (
    claim_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    case_id         UUID NOT NULL REFERENCES crm_case(case_id),
    stage           SMALLINT CHECK (stage BETWEEN 1 AND 8),   -- 8-stage VA lifecycle (Blueprint)
    intent_to_file_date DATE,
    accredited_rep_note TEXT           -- directory info only; the app never selects a POA
);
CREATE TABLE claim_issue (
    issue_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    claim_id        UUID NOT NULL REFERENCES claim(claim_id),
    label           TEXT NOT NULL,     -- user-reported; never an AI diagnosis or nexus
    origin          TEXT NOT NULL CHECK (origin IN ('document_fact','user_statement','external_authority','ai_inference','calculation'))
);
CREATE TABLE claim_evidence (
    evidence_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    claim_id        UUID NOT NULL REFERENCES claim(claim_id),
    document_id     UUID REFERENCES document(document_id),
    gap_note        TEXT
);
CREATE TABLE symptom_log (
    symptom_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id       UUID NOT NULL REFERENCES person_profile(person_id),
    logged_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    entry           TEXT NOT NULL,     -- classification V4/V5; never leaves Health Vault by default
    classification  TEXT NOT NULL DEFAULT 'V4' CHECK (classification IN ('V4','V5'))
);

CREATE TABLE institution (
    institution_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    jurisdiction_id UUID REFERENCES jurisdiction(jurisdiction_id),
    name            TEXT NOT NULL, kind TEXT, yellow_ribbon BOOLEAN, source_id UUID REFERENCES source_record(source_id)
);
CREATE TABLE education_program (
    program_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    institution_id  UUID NOT NULL REFERENCES institution(institution_id),
    name TEXT NOT NULL, tuition NUMERIC(10,2), fees NUMERIC(10,2), va_approved BOOLEAN
);
CREATE TABLE education_funding_stack (
    stack_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id       UUID NOT NULL REFERENCES person_profile(person_id),
    program_id      UUID NOT NULL REFERENCES education_program(program_id),
    components      JSONB NOT NULL,    -- tuition, fees, housing, aid, remaining gap
    stack_status    TEXT NOT NULL CHECK (stack_status IN ('STACKABLE_VERIFIED','POSSIBLY_STACKABLE_CONFIRM',
                        'ELECTION_REQUIRED','POTENTIAL_CONFLICT','UNKNOWN_HUMAN_VERIFICATION_REQUIRED')),
    ruleset_version TEXT NOT NULL      -- calculations are versioned and reproducible (v4.0 §32)
);

CREATE TABLE referral (               -- a phone number shown is NOT a completed referral (v4.0 §38)
    referral_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    case_id         UUID NOT NULL REFERENCES crm_case(case_id),
    resource_id     UUID NOT NULL REFERENCES resource(resource_id),
    consent_id      UUID REFERENCES consent_record(consent_id),
    status          TEXT NOT NULL DEFAULT 'recommended' CHECK (status IN ('recommended','consent_requested','consented',
                        'pending','sent','received','contacted','accepted','scheduled','enrolled_attended','completed',
                        'outcome_recorded','follow_up','closed','declined_by_user','declined_by_provider',
                        'no_response','stalled','cancelled')),
    next_action     TEXT, due_date DATE, outcome TEXT
    -- no lifetime UNIQUE(person, resource): legitimate repeat referrals must be allowed (v4.0 §87)
);
CREATE TABLE referral_status_event (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    referral_id     UUID NOT NULL REFERENCES referral(referral_id),
    from_status TEXT, to_status TEXT NOT NULL, occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

DO $$ DECLARE t TEXT; BEGIN
  FOREACH t IN ARRAY ARRAY['source_record','policy_version','document','extracted_fact','claim','claim_issue','claim_evidence',
      'symptom_log','institution','education_program','education_funding_stack','referral','referral_status_event'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('CREATE POLICY tenant_isolation_%1$s ON %1$I USING (tenant_id = current_setting(''vetbuddy.tenant_id'')::uuid)', t);
  END LOOP;
END $$;
