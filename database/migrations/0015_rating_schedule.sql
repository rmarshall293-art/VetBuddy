-- 0015 — 38 CFR Part 4 rating schedule as V0 reference data (additive only).
--
-- 737 diagnostic codes and their criteria text, transcribed from the 2020
-- edition. Reference for explaining how VA describes criteria; never applied
-- to a veteran's symptoms or records (governance §5). No row is VERIFIED until
-- a named reviewer re-checks it against current eCFR; the digestive codes are
-- SUPERSEDED (38 CFR 4.110-4.114 revised 2024-05-19). There is deliberately no
-- symptom or keyword column: mapping symptoms to codes is prohibited.

CREATE TABLE ref.rating_code (
  code          TEXT PRIMARY KEY CHECK (code ~ '^[0-9]{4}$'),
  name          TEXT NOT NULL,
  body_system   TEXT NOT NULL,
  subsection    TEXT,
  cfr_section   TEXT,
  notes         TEXT,
  has_criteria  BOOLEAN NOT NULL,
  status        ref.record_status NOT NULL,
  status_note   TEXT,
  source_ids    TEXT[] NOT NULL,
  verified_by   TEXT,
  verified_on   DATE,
  CHECK (status <> 'VERIFIED' OR (verified_by IS NOT NULL AND verified_on IS NOT NULL))
);

CREATE TABLE ref.rating_criterion (
  criterion_id  TEXT PRIMARY KEY,
  code          TEXT NOT NULL REFERENCES ref.rating_code(code),
  position      SMALLINT NOT NULL CHECK (position >= 0),
  percent       SMALLINT NOT NULL CHECK (percent BETWEEN 0 AND 100 AND percent % 10 = 0),
  criteria_text TEXT NOT NULL,
  UNIQUE (code, position)
);

CREATE TRIGGER rating_code_sources BEFORE INSERT OR UPDATE ON ref.rating_code
  FOR EACH ROW EXECUTE FUNCTION ref.assert_sources();

CREATE OR REPLACE VIEW ref.v_status_posture AS
SELECT 'directory_entry' AS tbl, status::text, count(*) FROM ref.directory_entry GROUP BY status
UNION ALL SELECT 'benefit_lead', status::text, count(*) FROM ref.benefit_lead GROUP BY status
UNION ALL SELECT 'rate', status::text, count(*) FROM ref.rate GROUP BY status
UNION ALL SELECT 'statistic', status::text, count(*) FROM ref.statistic GROUP BY status
UNION ALL SELECT 'rule_lead', status::text, count(*) FROM ref.rule_lead GROUP BY status
UNION ALL SELECT 'timeline_window', status::text, count(*) FROM ref.timeline_window GROUP BY status
UNION ALL SELECT 'rating_code', status::text, count(*) FROM ref.rating_code GROUP BY status;

-- Same zero-PII guard as 0011, re-run so the new tables are covered.
DO $$
DECLARE bad TEXT;
BEGIN
  SELECT string_agg(table_name || '.' || column_name, ', ') INTO bad
    FROM information_schema.columns
   WHERE table_schema = 'ref'
     AND column_name IN ('tenant_id','person_id','user_id','email','ssn','dob','date_of_birth',
                         'first_name','last_name','contact_name','staff_name','keywords','symptoms');
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'ref schema must hold no person, tenant or symptom columns: %', bad;
  END IF;
END $$;

GRANT SELECT ON ref.rating_code, ref.rating_criterion TO vetbuddy_app;
