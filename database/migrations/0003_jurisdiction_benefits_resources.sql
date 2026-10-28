-- Plane 4: Source Intelligence. This is the "unified for 50 states" table set.
-- ONE schema for every jurisdiction. What differs is data + verification_status.

CREATE TABLE jurisdiction (
    jurisdiction_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code              TEXT UNIQUE NOT NULL,   -- 'AL', 'PR', 'GU', 'FEDERAL', etc.
    name              TEXT NOT NULL,
    kind              TEXT NOT NULL CHECK (kind IN ('federal','state','territory','tribal','local')),
    -- THE gate for "keep the matcher for 50 states but disclaim the unverified ones"
    verification_status TEXT NOT NULL DEFAULT 'unverified'
                        CHECK (verification_status IN ('unverified','in_review','verified')),
    verified_at       TIMESTAMPTZ,
    verified_by       TEXT
);

-- Data Trust Card, inlined onto every sourced fact rather than a separate
-- joined table per row — every benefit/resource carries its own provenance.
CREATE TABLE benefit (
    benefit_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenant(tenant_id),
    jurisdiction_id   UUID NOT NULL REFERENCES jurisdiction(jurisdiction_id),
    name              TEXT NOT NULL,
    category          TEXT NOT NULL,   -- education, disability, employment, housing, family, etc.
    program_type      TEXT NOT NULL CHECK (program_type IN (
                            'statutory_entitlement','regulatory_entitlement','appropriation_subject',
                            'competitive_scholarship','agency_waiver','institutional_policy',
                            'pilot_temporary','expired_suspended'
                        )),
    -- Data Trust Card fields — required, not optional, at insert
    source_citation   TEXT NOT NULL,     -- e.g. "38 U.S.C. § 3311" or state statute
    source_tier       SMALLINT NOT NULL CHECK (source_tier BETWEEN 1 AND 4),
    official_url      TEXT NOT NULL,
    effective_date    DATE,
    last_verified     DATE NOT NULL,
    next_review_due   DATE NOT NULL,
    CHECK (source_tier <= 3 OR program_type = 'pilot_temporary')  -- tier-4 alone can't ground a real program
);

CREATE TABLE eligibility_rule (
    rule_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    benefit_id        UUID NOT NULL REFERENCES benefit(benefit_id),
    field             TEXT NOT NULL,          -- e.g. 'component', 'discharge_status', 'residency_months'
    operator          TEXT NOT NULL CHECK (operator IN ('eq','neq','gte','lte','in','not_in')),
    expected_value    JSONB NOT NULL,
    -- tri-state discipline (defect #1-#3 in the real system): a rule can
    -- never resolve to a denial from a merely-unknown fact. Enforce in the
    -- evaluator, this column just documents intent.
    unknown_handling  TEXT NOT NULL DEFAULT 'defer' CHECK (unknown_handling = 'defer')
);

CREATE TABLE resource (
    resource_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenant(tenant_id),
    jurisdiction_id   UUID NOT NULL REFERENCES jurisdiction(jurisdiction_id),
    name              TEXT NOT NULL,
    -- category covers the new asset types in one table, not new tables per type
    category          TEXT NOT NULL CHECK (category IN (
                            'healthcare','mental_health','housing','employment','education',
                            'legal','family_survivor','women_veteran','guard_reserve',
                            'installation_base','financial','crisis','recreation','citizenship'
                        )),
    services          TEXT[],
    eligibility_notes TEXT,
    contact_method    TEXT,
    source_citation   TEXT NOT NULL,
    source_tier       SMALLINT NOT NULL CHECK (source_tier BETWEEN 1 AND 4),
    last_verified     DATE NOT NULL,
    capacity_status   TEXT
);

ALTER TABLE benefit ENABLE ROW LEVEL SECURITY;
ALTER TABLE resource ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_benefit ON benefit
    USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);
CREATE POLICY tenant_isolation_resource ON resource
    USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);

-- Seed: federal + all 56 jurisdictions, unverified until reviewed.
-- Alabama is the one row flipped to 'verified' once its 8 rules are confirmed.
INSERT INTO jurisdiction (code, name, kind, verification_status) VALUES
 ('FEDERAL','United States (Federal)','federal','unverified'),
 ('AL','Alabama','state','unverified'), -- flip to 'verified' after Step 7 sign-off
 ('AK','Alaska','state','unverified'), ('AZ','Arizona','state','unverified'),
 ('AR','Arkansas','state','unverified'), ('CA','California','state','unverified'),
 ('CO','Colorado','state','unverified'), ('CT','Connecticut','state','unverified'),
 ('DE','Delaware','state','unverified'), ('FL','Florida','state','unverified'),
 ('GA','Georgia','state','unverified'), ('HI','Hawaii','state','unverified'),
 ('ID','Idaho','state','unverified'), ('IL','Illinois','state','unverified'),
 ('IN','Indiana','state','unverified'), ('IA','Iowa','state','unverified'),
 ('KS','Kansas','state','unverified'), ('KY','Kentucky','state','unverified'),
 ('LA','Louisiana','state','unverified'), ('ME','Maine','state','unverified'),
 ('MD','Maryland','state','unverified'), ('MA','Massachusetts','state','unverified'),
 ('MI','Michigan','state','unverified'), ('MN','Minnesota','state','unverified'),
 ('MS','Mississippi','state','unverified'), ('MO','Missouri','state','unverified'),
 ('MT','Montana','state','unverified'), ('NE','Nebraska','state','unverified'),
 ('NV','Nevada','state','unverified'), ('NH','New Hampshire','state','unverified'),
 ('NJ','New Jersey','state','unverified'), ('NM','New Mexico','state','unverified'),
 ('NY','New York','state','unverified'), ('NC','North Carolina','state','unverified'),
 ('ND','North Dakota','state','unverified'), ('OH','Ohio','state','unverified'),
 ('OK','Oklahoma','state','unverified'), ('OR','Oregon','state','unverified'),
 ('PA','Pennsylvania','state','unverified'), ('RI','Rhode Island','state','unverified'),
 ('SC','South Carolina','state','unverified'), ('SD','South Dakota','state','unverified'),
 ('TN','Tennessee','state','unverified'), ('TX','Texas','state','unverified'),
 ('UT','Utah','state','unverified'), ('VT','Vermont','state','unverified'),
 ('VA','Virginia','state','unverified'), ('WA','Washington','state','unverified'),
 ('WV','West Virginia','state','unverified'), ('WI','Wisconsin','state','unverified'),
 ('WY','Wyoming','state','unverified'), ('DC','District of Columbia','territory','unverified'),
 ('PR','Puerto Rico','territory','unverified'), ('GU','Guam','territory','unverified'),
 ('VI','U.S. Virgin Islands','territory','unverified'),
 ('AS','American Samoa','territory','unverified'),
 ('MP','Northern Mariana Islands','territory','unverified');
