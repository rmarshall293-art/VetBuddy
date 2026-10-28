-- Career Finder / MOS Translation / Resume Builder.
-- NOTE: "work_style_assessment" is intentionally generic, not "DISC" —
-- DiSC is a licensed trademarked instrument. See docs/ARCHITECTURE.md §5
-- before writing scoring logic against this table.

CREATE TABLE mos_crosswalk (
    crosswalk_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch            TEXT NOT NULL,
    mos_code          TEXT NOT NULL,          -- MOS/AFSC/Rating/NEC
    onet_soc_code     TEXT NOT NULL,          -- public O*NET/CareerOneStop code, not proprietary
    civilian_title    TEXT NOT NULL,
    source_citation   TEXT NOT NULL DEFAULT 'O*NET / CareerOneStop military crosswalk',
    last_verified     DATE NOT NULL,
    UNIQUE (branch, mos_code, onet_soc_code)
);

CREATE TABLE career_profile (
    career_profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id         UUID NOT NULL REFERENCES person_profile(person_id),
    target_occupations TEXT[],
    location_preference TEXT,
    salary_target_min  INTEGER,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE work_style_assessment (
    assessment_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id         UUID NOT NULL REFERENCES person_profile(person_id),
    instrument_name   TEXT NOT NULL,   -- name your own instrument here once decided
    instrument_version TEXT NOT NULL,
    -- store raw scored dimensions generically; do not hardcode DiSC's
    -- four-letter output shape into the schema
    dimension_scores  JSONB NOT NULL,
    taken_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    scoring_is_transparent BOOLEAN NOT NULL DEFAULT true  -- v4.0 §31: no opaque scoring
);

CREATE TABLE job_match (
    job_match_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenant(tenant_id),
    career_profile_id UUID NOT NULL REFERENCES career_profile(career_profile_id),
    onet_soc_code     TEXT NOT NULL,
    match_score       NUMERIC(4,3) NOT NULL CHECK (match_score BETWEEN 0 AND 1),
    match_basis       JSONB NOT NULL,   -- which factors contributed — never an opaque black-box score
    generated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE resume_document (
    resume_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id         UUID NOT NULL REFERENCES person_profile(person_id),
    source_dd214_doc_id UUID,           -- references documents table (out of scope this pass)
    generated_from    TEXT NOT NULL DEFAULT 'dd214',
    content           JSONB NOT NULL,   -- structured sections, not a rendered blob
    status            TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','user_approved','exported')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE career_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_style_assessment ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_match ENABLE ROW LEVEL SECURITY;
ALTER TABLE resume_document ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_career ON career_profile USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);
CREATE POLICY tenant_isolation_assessment ON work_style_assessment USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);
CREATE POLICY tenant_isolation_jobmatch ON job_match USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);
CREATE POLICY tenant_isolation_resume ON resume_document USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);
