-- 0019 — Rating formulas of 38 CFR Part 4, and which codes they rate (additive only).
--
-- Much of the current schedule rates codes by a shared formula instead of rows under
-- each code: the General Rating Formula for Mental Disorders (DCs 9201-9440), the
-- spine, heart, skin, eye, lung, infectious-disease and seizure formulas, and the
-- genitourinary dysfunction ratings of 4.115a. scripts/build_rating_schedule.py reads
-- them from the saved eCFR text and links a code to a formula only where the
-- regulation says so in words. Reference only; never applied to a veteran's symptoms
-- or records (governance §5). Rows are SOURCE_CHECKED, never VERIFIED without a
-- named reviewer.

CREATE TABLE ref.rating_formula (
  formula_id   TEXT PRIMARY KEY CHECK (formula_id ~ '^cfr4_[0-9a-z_]+\.[a-z0-9_]+$'),
  cfr_section  TEXT NOT NULL,
  title        TEXT NOT NULL,
  notes        TEXT,
  status       ref.record_status NOT NULL,
  source_ids   TEXT[] NOT NULL,
  verified_by  TEXT,
  verified_on  DATE,
  CHECK (status <> 'VERIFIED' OR (verified_by IS NOT NULL AND verified_on IS NOT NULL))
);

CREATE TABLE ref.rating_formula_criterion (
  criterion_id  TEXT PRIMARY KEY,
  formula_id    TEXT NOT NULL REFERENCES ref.rating_formula(formula_id),
  position      SMALLINT NOT NULL CHECK (position >= 0),
  percent       SMALLINT NOT NULL CHECK (percent BETWEEN 0 AND 100 AND percent % 10 = 0),
  criteria_text TEXT NOT NULL,
  UNIQUE (formula_id, position)
);

CREATE TABLE ref.rating_code_formula (
  code        TEXT NOT NULL REFERENCES ref.rating_code(code),
  formula_id  TEXT NOT NULL REFERENCES ref.rating_formula(formula_id),
  PRIMARY KEY (code, formula_id)
);

-- Diagnostic codes a code's own text cites ("Rate as esophagus, stricture of (DC 7203)").
ALTER TABLE ref.rating_code ADD COLUMN cited_codes TEXT[] NOT NULL DEFAULT '{}';

CREATE TRIGGER rating_formula_sources BEFORE INSERT OR UPDATE ON ref.rating_formula
  FOR EACH ROW EXECUTE FUNCTION ref.assert_sources();

CREATE OR REPLACE VIEW ref.v_status_posture AS
SELECT 'directory_entry' AS tbl, status::text, count(*) FROM ref.directory_entry GROUP BY status
UNION ALL SELECT 'benefit_lead', status::text, count(*) FROM ref.benefit_lead GROUP BY status
UNION ALL SELECT 'rate', status::text, count(*) FROM ref.rate GROUP BY status
UNION ALL SELECT 'statistic', status::text, count(*) FROM ref.statistic GROUP BY status
UNION ALL SELECT 'rule_lead', status::text, count(*) FROM ref.rule_lead GROUP BY status
UNION ALL SELECT 'timeline_window', status::text, count(*) FROM ref.timeline_window GROUP BY status
UNION ALL SELECT 'rating_code', status::text, count(*) FROM ref.rating_code GROUP BY status
UNION ALL SELECT 'rating_formula', status::text, count(*) FROM ref.rating_formula GROUP BY status;

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

GRANT SELECT ON ref.rating_formula, ref.rating_formula_criterion, ref.rating_code_formula TO vetbuddy_app;
