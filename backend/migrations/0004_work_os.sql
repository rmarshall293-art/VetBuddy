-- 0004 Work OS: Master Mission -> Master Case -> lanes -> tasks.
--
-- One Master Mission per routing run, one Master Case per mission. Rows are
-- reachable only by their owner, inside their tenant, while `plan_storage`
-- consent is active. Because DELETE ... WHERE also applies the SELECT policy,
-- deletion happens while consent is still live: the API's "revoke and delete"
-- deletes first, then revokes, in one transaction.
--
-- Privacy Mode A (guest) never reaches these tables. Mode C (managed case) is
-- unreachable by design until its review completes: the CHECK refuses it.
-- `router_input` holds declared, non-health routing facts only (V2 at most).

CREATE TABLE vb.missions (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id        uuid NOT NULL,
  user_id          uuid NOT NULL,
  privacy_mode     text NOT NULL DEFAULT 'B' CONSTRAINT mission_mode_b_only CHECK (privacy_mode = 'B'),
  policy_version   text NOT NULL,
  input_hash       text NOT NULL CHECK (input_hash ~ '^[0-9a-f]{64}$'),
  router_input     jsonb NOT NULL,
  as_of            date NOT NULL,
  stage            text NOT NULL,
  track            text NOT NULL,
  notices          jsonb NOT NULL DEFAULT '[]',
  status           text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
  created_at       timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, user_id) REFERENCES vb.users(tenant_id, id),
  UNIQUE (tenant_id, id)
);

CREATE TABLE vb.master_cases (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    uuid NOT NULL,
  user_id      uuid NOT NULL,
  mission_id   uuid NOT NULL UNIQUE,
  status       text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
  created_at   timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, mission_id) REFERENCES vb.missions(tenant_id, id) ON DELETE CASCADE,
  UNIQUE (tenant_id, id)
);

CREATE TABLE vb.case_lanes (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   uuid NOT NULL,
  user_id     uuid NOT NULL,
  case_id     uuid NOT NULL,
  lane        text NOT NULL,
  position    int  NOT NULL,
  FOREIGN KEY (tenant_id, case_id) REFERENCES vb.master_cases(tenant_id, id) ON DELETE CASCADE,
  UNIQUE (case_id, lane)
);

CREATE TABLE vb.tasks (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id            uuid NOT NULL,
  user_id              uuid NOT NULL,
  case_id              uuid NOT NULL,
  template_id          text NOT NULL,
  lane                 text NOT NULL,
  readiness_dimension  text NOT NULL,
  title                text NOT NULL,
  why                  text NOT NULL,
  confirm_with         text,
  priority             int  NOT NULL CHECK (priority BETWEEN 1 AND 9),
  status               text NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'done', 'cancelled')),
  version              int  NOT NULL DEFAULT 1,
  updated_at           timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, case_id) REFERENCES vb.master_cases(tenant_id, id) ON DELETE CASCADE,
  UNIQUE (case_id, template_id)
);

CREATE INDEX tasks_case ON vb.tasks (case_id);
CREATE INDEX missions_owner ON vb.missions (tenant_id, user_id, created_at DESC);

-- Owner + tenant + live consent. Same predicate on every Work OS table.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['missions', 'master_cases', 'case_lanes', 'tasks'] LOOP
    EXECUTE format('ALTER TABLE vb.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE vb.%I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format($p$CREATE POLICY %I ON vb.%I FOR SELECT TO vetbuddy_app
      USING (tenant_id = vb.current_tenant() AND user_id = vb.current_user_id() AND vb.has_consent('plan_storage'))$p$,
      t || '_read', t);
    EXECUTE format($p$CREATE POLICY %I ON vb.%I FOR INSERT TO vetbuddy_app
      WITH CHECK (tenant_id = vb.current_tenant() AND user_id = vb.current_user_id() AND vb.has_consent('plan_storage'))$p$,
      t || '_insert', t);
    EXECUTE format($p$CREATE POLICY %I ON vb.%I FOR UPDATE TO vetbuddy_app
      USING (tenant_id = vb.current_tenant() AND user_id = vb.current_user_id() AND vb.has_consent('plan_storage'))
      WITH CHECK (tenant_id = vb.current_tenant() AND user_id = vb.current_user_id())$p$,
      t || '_update', t);
    EXECUTE format($p$CREATE POLICY %I ON vb.%I FOR DELETE TO vetbuddy_app
      USING (tenant_id = vb.current_tenant() AND user_id = vb.current_user_id())$p$,
      t || '_delete', t);
  END LOOP;
END
$$;

GRANT SELECT, INSERT, DELETE ON vb.missions, vb.master_cases, vb.case_lanes, vb.tasks TO vetbuddy_app;
GRANT UPDATE (status) ON vb.missions, vb.master_cases TO vetbuddy_app;
GRANT UPDATE (status, version, updated_at) ON vb.tasks TO vetbuddy_app;

-- A child row must belong to the same user as its parent (FKs pin the tenant).
CREATE OR REPLACE FUNCTION vb.same_owner_as_parent() RETURNS trigger
  LANGUAGE plpgsql AS $$
DECLARE owner uuid;
BEGIN
  IF TG_TABLE_NAME = 'master_cases' THEN
    SELECT user_id INTO owner FROM vb.missions WHERE id = NEW.mission_id;
  ELSE
    SELECT user_id INTO owner FROM vb.master_cases WHERE id = NEW.case_id;
  END IF;
  IF owner IS DISTINCT FROM NEW.user_id THEN
    RAISE EXCEPTION 'owner mismatch on %', TG_TABLE_NAME USING ERRCODE = '42501';
  END IF;
  RETURN NEW;
END
$$;

CREATE TRIGGER master_cases_owner BEFORE INSERT ON vb.master_cases FOR EACH ROW EXECUTE FUNCTION vb.same_owner_as_parent();
CREATE TRIGGER case_lanes_owner   BEFORE INSERT ON vb.case_lanes   FOR EACH ROW EXECUTE FUNCTION vb.same_owner_as_parent();
CREATE TRIGGER tasks_owner        BEFORE INSERT ON vb.tasks        FOR EACH ROW EXECUTE FUNCTION vb.same_owner_as_parent();
