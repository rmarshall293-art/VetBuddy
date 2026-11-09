-- 0010 — Foreclosed consent purposes (closes CB-03).
-- Source: MASTER_BUILD_PROMPT.md §5.2 ("Nine purposes exist as rows marked
-- foreclosed, enforced by trigger, not policy prose"); Master Record §4.1.
-- A grant naming one of these fails even from the schema owner.

ALTER TABLE consent_purpose
  ADD COLUMN foreclosed BOOLEAN NOT NULL DEFAULT false,
  ADD CONSTRAINT foreclosed_never_allowed CHECK (NOT (foreclosed AND allowed));

INSERT INTO consent_purpose (purpose, description, data_classes, allowed, foreclosed) VALUES
 ('sale_of_personal_information',      'Sale of personal information',                          '{}', false, true),
 ('third_party_marketing',             'Third-party marketing',                                 '{}', false, true),
 ('insurance_underwriting',            'Insurance underwriting',                                '{}', false, true),
 ('credit_or_lending_decisions',       'Credit or lending decisions',                           '{}', false, true),
 ('third_party_employment_screening',  'Third-party employment screening',                      '{}', false, true),
 ('disability_based_occupation_filtering', 'Disability-based occupation filtering (ADA)',       '{}', false, true),
 ('proactive_law_enforcement_disclosure',  'Proactive law-enforcement disclosure',              '{}', false, true),
 ('training_external_models',          'Training external models',                              '{}', false, true),
 ('reidentification_of_aggregates',    'Re-identification of aggregates',                       '{}', false, true);

CREATE FUNCTION refuse_foreclosed_consent() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM consent_purpose WHERE purpose = NEW.purpose AND (foreclosed OR NOT allowed)) THEN
    RAISE EXCEPTION 'consent purpose % is foreclosed or not offered', NEW.purpose
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;

CREATE TRIGGER consent_purpose_not_foreclosed BEFORE INSERT OR UPDATE OF purpose ON consent_record
  FOR EACH ROW EXECUTE FUNCTION refuse_foreclosed_consent();

-- A foreclosed row can never be reopened or deleted.
CREATE FUNCTION protect_foreclosed_purpose() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.foreclosed THEN
    RAISE EXCEPTION 'foreclosed purpose % is immutable', OLD.purpose USING ERRCODE = 'check_violation';
  END IF;
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END $$;
CREATE TRIGGER consent_purpose_foreclosed_immutable BEFORE UPDATE OR DELETE ON consent_purpose
  FOR EACH ROW EXECUTE FUNCTION protect_foreclosed_purpose();
