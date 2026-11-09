-- 0018 — Second rating column for the 38 CFR Part 4 schedule (additive only).
--
-- 38 CFR 4.69 rates the dominant ("major") and non-dominant ("minor") upper
-- extremity separately, so many codes in 4.71a, 4.73 and 4.124a have two
-- rating columns. Migration 0017 had one, and the 2020 transcription put the
-- minor figure in `percent` while leaving the major figure in the text.
-- From this migration, `percent` is the major (dominant) side and
-- `percent_minor` the minor side where the table has two columns; it is NULL
-- where the table has one. The rows themselves are re-transcribed from eCFR by
-- scripts/rebuild_rating_criteria.py and stay UNVERIFIED (reference only;
-- never applied to a veteran's symptoms or records, governance §5).

ALTER TABLE ref.rating_criterion
  ADD COLUMN percent_minor SMALLINT
    CHECK (percent_minor BETWEEN 0 AND 100 AND percent_minor % 10 = 0);

COMMENT ON COLUMN ref.rating_criterion.percent IS
  'Rating in percent. Where percent_minor is set, this is the major (dominant) side (38 CFR 4.69).';
COMMENT ON COLUMN ref.rating_criterion.percent_minor IS
  'Minor (non-dominant) side rating where the official table has two columns; NULL otherwise.';
