-- Delegated access, Share Cards, community privacy wall, comms, finance runs, life events, immutability triggers.
CREATE TABLE delegated_access (       -- scope-, time-, purpose-limited, revocable, audited (v4.0 §69)
    delegation_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    grantor_user_id UUID NOT NULL REFERENCES app_user(user_id),
    grantee_user_id UUID NOT NULL REFERENCES app_user(user_id),
    scope           TEXT[] NOT NULL, purpose TEXT NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL, revoked_at TIMESTAMPTZ,
    CHECK (grantor_user_id <> grantee_user_id)
);
CREATE TABLE share_card (             -- the only path protected data may enter Community (v4.0 §42)
    share_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(tenant_id),
    user_id         UUID NOT NULL REFERENCES app_user(user_id),
    exact_fields    JSONB NOT NULL, recipient TEXT NOT NULL, purpose TEXT NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL, approved_at TIMESTAMPTZ
);
CREATE TABLE community_group (
    group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(tenant_id),
    kind TEXT NOT NULL CHECK (kind IN ('national','jurisdiction','installation','branch_component','transition','spouse_family','guard_reserve','women_veterans','caregiver','survivor')),
    name TEXT NOT NULL, jurisdiction_id UUID REFERENCES jurisdiction(jurisdiction_id)
);
CREATE TABLE community_post (         -- deliberately NO foreign key to claims/health/case tables
    post_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(tenant_id),
    group_id UUID NOT NULL REFERENCES community_group(group_id),
    author_user_id UUID NOT NULL REFERENCES app_user(user_id),
    body TEXT NOT NULL, moderation_status TEXT NOT NULL DEFAULT 'pending' CHECK (moderation_status IN ('pending','approved','removed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE notification (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(tenant_id),
    user_id UUID NOT NULL REFERENCES app_user(user_id),
    priority TEXT NOT NULL CHECK (priority IN ('critical','important','recommended','informational')),
    channel TEXT NOT NULL CHECK (channel IN ('in_app','email','sms','push')),
    template TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE calculation_run (        -- MoneyLife: versioned, reproducible, source-linked, timestamped
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id UUID NOT NULL REFERENCES person_profile(person_id),
    calculation_type TEXT NOT NULL, ruleset_version TEXT NOT NULL, source_version TEXT,
    effective_date DATE NOT NULL, input_summary JSONB NOT NULL, output JSONB NOT NULL,
    data_status TEXT NOT NULL DEFAULT 'educational', run_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE life_event (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(tenant_id),
    person_id UUID NOT NULL REFERENCES person_profile(person_id),
    kind TEXT NOT NULL, occurred_on DATE NOT NULL, user_authorized BOOLEAN NOT NULL DEFAULT false
);

DO $$ DECLARE t TEXT; BEGIN
  FOREACH t IN ARRAY ARRAY['delegated_access','share_card','community_group','community_post','notification','calculation_run','life_event'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('CREATE POLICY tenant_isolation_%1$s ON %1$I USING (tenant_id = current_setting(''vetbuddy.tenant_id'')::uuid)', t);
  END LOOP;
END $$;

-- Integrity: enforce what earlier migrations only documented.
CREATE FUNCTION forbid_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '% is append-only', TG_TABLE_NAME; END $$;
CREATE TRIGGER audit_event_append_only BEFORE UPDATE OR DELETE ON audit_event
    FOR EACH ROW EXECUTE FUNCTION forbid_mutation();
CREATE FUNCTION forbid_document_original_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.storage_key IS DISTINCT FROM OLD.storage_key OR NEW.sha256 IS DISTINCT FROM OLD.sha256 THEN
    RAISE EXCEPTION 'original document bytes are immutable';
  END IF; RETURN NEW;
END $$;
CREATE TRIGGER document_original_immutable BEFORE UPDATE ON document
    FOR EACH ROW EXECUTE FUNCTION forbid_document_original_change();
