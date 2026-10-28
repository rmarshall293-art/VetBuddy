-- Plane 1: Trust & Identity
-- Every table below carries tenant_id from creation. This closes the
-- "application_case had no tenant_id" defect by making it structurally
-- impossible to omit on any table added later in this file set.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE tenant (
    tenant_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             TEXT NOT NULL,
    kind             TEXT NOT NULL CHECK (kind IN ('individual','organization','partner')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE app_user (
    user_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL REFERENCES tenant(tenant_id),
    email            TEXT UNIQUE,
    role             TEXT NOT NULL DEFAULT 'USER',
    -- privacy mode governs what may ever be persisted for this user
    privacy_mode     TEXT NOT NULL DEFAULT 'B' CHECK (privacy_mode IN ('A','B','C')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at       TIMESTAMPTZ
);

CREATE TABLE consent_record (
    consent_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL REFERENCES tenant(tenant_id),
    user_id          UUID NOT NULL REFERENCES app_user(user_id),
    purpose          TEXT NOT NULL,
    data_categories  TEXT[] NOT NULL,
    granted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at       TIMESTAMPTZ
);

-- Append-only. Never UPDATE or DELETE a row here in application code.
CREATE TABLE audit_event (
    audit_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL REFERENCES tenant(tenant_id),
    actor_user_id    UUID REFERENCES app_user(user_id),
    actor_agent_id   TEXT,
    action           TEXT NOT NULL,
    resource_type    TEXT NOT NULL,
    resource_id      UUID,
    old_value        JSONB,
    new_value        JSONB,
    reason           TEXT,
    prev_hash        TEXT,
    row_hash         TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Row-level security is enabled at creation, not bolted on later.
ALTER TABLE app_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_record ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_event ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_user ON app_user
    USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);
CREATE POLICY tenant_isolation_consent ON consent_record
    USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);
CREATE POLICY tenant_isolation_audit ON audit_event
    USING (tenant_id = current_setting('vetbuddy.tenant_id')::uuid);
