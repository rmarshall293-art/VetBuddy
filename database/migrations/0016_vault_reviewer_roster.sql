-- 0016 — Reviewer roster for the Benefit Vault (gate G1; owner decision 2026-10-29; ADR 0006).
--
-- Before this, any well-formed handle could be written as verified_by. Now a
-- record becomes VERIFIED only by a handle on the roster that is active and
-- whose scope covers the record's jurisdiction, and every review is logged.
--
-- * The project owner keeps the roster (config/reviewer_roster.yaml, synced by
--   scripts/vault_review.py). Handles only: never a name, email or phone. The
--   handle pattern refuses '@', spaces and capitals.
-- * Reviewers are accredited people: VA-accredited VSO representatives, claims
--   agents or attorneys, or state veterans agency staff.
-- * A reviewer's scope is a list of jurisdiction codes ('AL', 'US', …) or '*'.
-- * The check fires when a record becomes VERIFIED or its reviewer changes, so
--   retiring a reviewer later does not silently erase past reviews; withdrawing
--   a review is its own logged action.
-- * ref.vault_review_event is append-only for everyone (owner included).
-- * The app role reads neither table: the API learns about reviews only
--   through ref.vault_benefit (load_reviews), as before.

CREATE TABLE ref.vault_reviewer (
  handle      TEXT PRIMARY KEY CHECK (handle ~ '^[a-z0-9][a-z0-9._-]{1,63}$'),
  role        TEXT NOT NULL CHECK (role IN ('accredited_vso_representative', 'accredited_claims_agent',
                                            'accredited_attorney', 'state_veterans_agency')),
  scope       TEXT[] NOT NULL CHECK (cardinality(scope) >= 1
                                     AND array_to_string(scope, ',') ~ '^(\*|[A-Z]{2})(,[A-Z]{2})*$'),
  added_on    DATE NOT NULL,
  added_by    TEXT NOT NULL CHECK (added_by = 'project_owner'),
  active      BOOLEAN NOT NULL DEFAULT true,
  retired_on  DATE,
  CONSTRAINT retired_has_date CHECK (active OR retired_on IS NOT NULL)
);
REVOKE ALL ON ref.vault_reviewer FROM PUBLIC;

CREATE TABLE ref.vault_review_event (
  event_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  benefit_id    TEXT NOT NULL,
  action        TEXT NOT NULL CHECK (action IN ('VERIFIED', 'WITHDRAWN')),
  handle        TEXT NOT NULL CHECK (handle ~ '^[a-z0-9][a-z0-9._-]{1,63}$'),
  content_hash  TEXT NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
  on_date       DATE NOT NULL,
  recorded_at   TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
REVOKE ALL ON ref.vault_review_event FROM PUBLIC;

CREATE FUNCTION ref.vault_review_event_append_only() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  RAISE EXCEPTION 'ref.vault_review_event is append-only' USING ERRCODE = '42501';
END $$;
CREATE TRIGGER vault_review_event_append_only BEFORE UPDATE OR DELETE ON ref.vault_review_event
  FOR EACH ROW EXECUTE FUNCTION ref.vault_review_event_append_only();
CREATE TRIGGER vault_review_event_no_truncate BEFORE TRUNCATE ON ref.vault_review_event
  FOR EACH STATEMENT EXECUTE FUNCTION ref.vault_review_event_append_only();

-- A VERIFIED mark needs an active roster reviewer whose scope covers the record.
CREATE FUNCTION ref.vault_benefit_reviewer_check() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE r RECORD;
BEGIN
  IF NEW.record_status = 'VERIFIED'
     AND (TG_OP = 'INSERT' OR OLD.record_status IS DISTINCT FROM 'VERIFIED'
          OR NEW.verified_by IS DISTINCT FROM OLD.verified_by) THEN
    SELECT * INTO r FROM ref.vault_reviewer WHERE handle = NEW.verified_by;
    IF NOT FOUND THEN
      RAISE EXCEPTION '% is not on the reviewer roster', NEW.verified_by USING ERRCODE = '23514';
    END IF;
    IF NOT r.active THEN
      RAISE EXCEPTION 'reviewer % is retired', NEW.verified_by USING ERRCODE = '23514';
    END IF;
    IF NOT ('*' = ANY (r.scope) OR NEW.jurisdiction = ANY (r.scope)) THEN
      RAISE EXCEPTION 'reviewer % may not review % records', NEW.verified_by, NEW.jurisdiction
        USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER vault_benefit_reviewer_check BEFORE INSERT OR UPDATE ON ref.vault_benefit
  FOR EACH ROW EXECUTE FUNCTION ref.vault_benefit_reviewer_check();

DO $postcheck$
BEGIN
  IF has_table_privilege('vetbuddy_app', 'ref.vault_reviewer', 'SELECT')
     OR has_table_privilege('vetbuddy_app', 'ref.vault_review_event', 'SELECT') THEN
    RAISE EXCEPTION 'the app role must not read the reviewer roster or review log';
  END IF;
  IF EXISTS (SELECT 1 FROM ref.vault_benefit WHERE record_status = 'VERIFIED') THEN
    RAISE EXCEPTION 'VERIFIED records exist with no roster: review them again through scripts/vault_review.py';
  END IF;
END
$postcheck$;
