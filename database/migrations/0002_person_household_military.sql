-- Plane 2 support: the person underneath missions/cases.

CREATE TABLE household (
    household_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL REFERENCES tenant(tenant_id)
);

CREATE TABLE person_profile (
    person_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL REFERENCES tenant(tenant_id),
    user_id          UUID REFERENCES app_user(user_id),
    household_id     UUID REFERENCES household(household_id),
    relationship     TEXT NOT NULL DEFAULT 'self'
                     CHECK (relationship IN ('self','spouse','dependent','caregiver','survivor')),
    -- minimum-necessary per Mode B; nothing here requires SSN
    display_name     TEXT,
    state_territory  TEXT,       -- current jurisdiction, FK added in 0003 after jurisdiction exists
    country          TEXT DEFAULT 'US',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE service_record (
    service_record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id          UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id          UUID NOT NULL REFERENCES person_profile(person_id),
    branch             TEXT NOT NULL,   -- Army, Navy, Marine Corps, Air Force, Space Force, Coast Guard
    component          TEXT NOT NULL CHECK (component IN (
                            'active_duty','national_guard','reserve','retired',
                            'retired_reserve_gray_area','separated','medically_separated'
                        )),
    legal_authority    TEXT,            -- Title 10 / Title 32 / State Active Duty — never left blank if component involves Guard/Reserve
    mos_afsc_rating    TEXT,            -- occupation code, source for the career module
    pay_grade          TEXT,
    service_start      DATE,
    service_end        DATE,
    discharge_status   TEXT,
    UNIQUE (person_id, service_start, branch)
);

ALTER TABLE person_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_record ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_person ON person_profile
    USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);
CREATE POLICY tenant_isolation_service ON service_record
    USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);

-- Guard/Reserve status must never be inferred from component alone (v4.0 §34).
-- legal_authority is required at the application layer whenever component
-- is national_guard or reserve — enforce in service code, not just here.
