-- 0005 Append-only, hash-chained audit and the transactional outbox.
--
-- Audit rows carry ids and codes only, never facts (I9). Each tenant has its
-- own chain: hash = sha256(prev_hash || canonical row). The chain is computed
-- by a definer trigger, so callers cannot choose their own hashes, and UPDATE,
-- DELETE and TRUNCATE are refused for every role, including the owner.
--
-- Outbox rows are written in the same transaction as the change they announce
-- (at-least-once delivery, idempotency key per event). No dispatcher exists
-- yet (gap G19); rows accumulate with dispatched_at NULL.

CREATE TABLE vb.audit_events (
  seq           bigserial PRIMARY KEY,
  tenant_id     uuid NOT NULL,
  actor_kind    text NOT NULL CHECK (actor_kind IN ('user', 'agent', 'human_reviewer', 'system')),
  actor_id      uuid,
  action        text NOT NULL CHECK (action ~ '^[a-z][a-z0-9_.]{2,63}$'),
  object_type   text NOT NULL CHECK (object_type ~ '^[a-z][a-z0-9_]{1,40}$'),
  object_id     uuid,
  reason_code   text CHECK (reason_code IS NULL OR reason_code ~ '^[A-Z][A-Z0-9_]{1,63}$'),
  trace_id      text CHECK (trace_id IS NULL OR trace_id ~ '^[0-9a-f]{32}$'),
  at            timestamptz NOT NULL DEFAULT now(),
  prev_hash     text NOT NULL DEFAULT '',
  hash          text NOT NULL DEFAULT ''
);

CREATE INDEX audit_events_tenant ON vb.audit_events (tenant_id, seq);

CREATE OR REPLACE FUNCTION vb.audit_chain() RETURNS trigger
  LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, vb AS $$
DECLARE prev text;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('vb.audit:' || NEW.tenant_id::text, 0));
  SELECT a.hash INTO prev FROM vb.audit_events a WHERE a.tenant_id = NEW.tenant_id ORDER BY a.seq DESC LIMIT 1;
  NEW.prev_hash := coalesce(prev, repeat('0', 64));
  NEW.at := now();
  NEW.hash := encode(sha256(convert_to(
    concat_ws('|', NEW.prev_hash, NEW.tenant_id, NEW.actor_kind, coalesce(NEW.actor_id::text, ''), NEW.action,
              NEW.object_type, coalesce(NEW.object_id::text, ''), coalesce(NEW.reason_code, ''),
              coalesce(NEW.trace_id, ''), to_char(NEW.at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')),
    'UTF8')), 'hex');
  RETURN NEW;
END
$$;

CREATE OR REPLACE FUNCTION vb.refuse_mutation() RETURNS trigger
  LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION '% is append-only', TG_TABLE_NAME USING ERRCODE = '42501';
END
$$;

CREATE TRIGGER audit_chain BEFORE INSERT ON vb.audit_events FOR EACH ROW EXECUTE FUNCTION vb.audit_chain();
CREATE TRIGGER audit_no_update BEFORE UPDATE OR DELETE ON vb.audit_events FOR EACH ROW EXECUTE FUNCTION vb.refuse_mutation();
CREATE TRIGGER audit_no_truncate BEFORE TRUNCATE ON vb.audit_events FOR EACH STATEMENT EXECUTE FUNCTION vb.refuse_mutation();

ALTER FUNCTION vb.audit_chain() OWNER TO vetbuddy_definer;

ALTER TABLE vb.audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE vb.audit_events FORCE ROW LEVEL SECURITY;

-- The API may append for the current tenant, as the current user or as system.
-- It may NOT read the audit trail (that is an operations-plane job).
CREATE POLICY audit_append ON vb.audit_events FOR INSERT TO vetbuddy_app
  WITH CHECK (tenant_id = vb.current_tenant() AND (actor_id IS NULL OR actor_id = vb.current_user_id()));
CREATE POLICY audit_chain_read ON vb.audit_events FOR SELECT TO vetbuddy_definer USING (true);

GRANT INSERT ON vb.audit_events TO vetbuddy_app;
GRANT USAGE ON SEQUENCE vb.audit_events_seq_seq TO vetbuddy_app;
GRANT SELECT ON vb.audit_events TO vetbuddy_definer;

CREATE TABLE vb.outbox (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id        uuid NOT NULL,
  event_type       text NOT NULL CHECK (event_type ~ '^[A-Z][A-Z0-9_]{2,63}$'),
  schema_version   text NOT NULL DEFAULT 'vetbuddy.event.v1',
  aggregate_type   text NOT NULL,
  aggregate_id     uuid NOT NULL,
  idempotency_key  text NOT NULL UNIQUE,
  classification   text NOT NULL DEFAULT 'V1' CHECK (classification IN ('V0', 'V1', 'V2')),
  payload          jsonb NOT NULL DEFAULT '{}',
  trace_id         text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  dispatched_at    timestamptz,
  attempts         int NOT NULL DEFAULT 0
);

ALTER TABLE vb.outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE vb.outbox FORCE ROW LEVEL SECURITY;
CREATE POLICY outbox_append ON vb.outbox FOR INSERT TO vetbuddy_app WITH CHECK (tenant_id = vb.current_tenant());
GRANT INSERT ON vb.outbox TO vetbuddy_app;
