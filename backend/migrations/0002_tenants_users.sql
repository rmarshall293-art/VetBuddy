-- 0002 Tenants and users (Trust & Identity plane).
--
-- A user row maps an identity-provider subject to a VetBuddy user inside one
-- tenant. Subjects are opaque IdP identifiers; no name, email or SSN is stored
-- here (R14: VetBuddy never stores an SSN).

CREATE TABLE vb.tenants (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug        text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9][a-z0-9-]{1,62}$'),
  name        text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE vb.users (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   uuid NOT NULL REFERENCES vb.tenants(id),
  subject     text NOT NULL CHECK (length(subject) BETWEEN 1 AND 200),
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, subject),
  UNIQUE (tenant_id, id)
);

ALTER TABLE vb.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE vb.tenants FORCE ROW LEVEL SECURITY;
ALTER TABLE vb.users   ENABLE ROW LEVEL SECURITY;
ALTER TABLE vb.users   FORCE ROW LEVEL SECURITY;

CREATE POLICY tenants_own ON vb.tenants FOR SELECT TO vetbuddy_app
  USING (id = vb.current_tenant());

CREATE POLICY users_self ON vb.users FOR SELECT TO vetbuddy_app
  USING (tenant_id = vb.current_tenant() AND id = vb.current_user_id());

-- Identity resolution (below) may look up any tenant by slug and create users.
CREATE POLICY tenants_resolver ON vb.tenants FOR SELECT TO vetbuddy_definer USING (true);
CREATE POLICY users_resolver_read ON vb.users FOR SELECT TO vetbuddy_definer USING (true);
CREATE POLICY users_resolver_insert ON vb.users FOR INSERT TO vetbuddy_definer WITH CHECK (true);

GRANT SELECT ON vb.tenants, vb.users TO vetbuddy_app;
GRANT SELECT ON vb.tenants TO vetbuddy_definer;
GRANT SELECT, INSERT ON vb.users TO vetbuddy_definer;

-- The default consumer tenant for Privacy Mode B (personal, private).
INSERT INTO vb.tenants (slug, name) VALUES ('public', 'VetBuddy personal accounts');

-- Identity resolution swap point. The API has already verified the token; this
-- maps (tenant slug, subject) to ids, creating the user on first sign-in. It
-- takes no free SQL and returns nothing for an
-- unknown tenant (the API turns that into 401).
CREATE OR REPLACE FUNCTION vb.resolve_principal(p_tenant_slug text, p_subject text)
  RETURNS TABLE (tenant_id uuid, user_id uuid)
  LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, vb AS $$
#variable_conflict use_column
DECLARE
  t uuid;
  u uuid;
BEGIN
  SELECT tn.id INTO t FROM vb.tenants tn WHERE tn.slug = p_tenant_slug;
  IF t IS NULL THEN
    RETURN;
  END IF;
  INSERT INTO vb.users AS us (tenant_id, subject) VALUES (t, p_subject)
    ON CONFLICT ON CONSTRAINT users_tenant_id_subject_key DO NOTHING;
  SELECT us.id INTO u FROM vb.users us WHERE us.tenant_id = t AND us.subject = p_subject;
  tenant_id := t;
  user_id := u;
  RETURN NEXT;
END
$$;

ALTER FUNCTION vb.resolve_principal(text, text) OWNER TO vetbuddy_definer;
REVOKE ALL ON FUNCTION vb.resolve_principal(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vb.resolve_principal(text, text) TO vetbuddy_app;
