"""Career Navigator core (ADR 0007). Adversarial by intent: each test tries to get
a fabricated, unauthorized, protected or health-informed statement or finding
through.

Sections:
  1. the specification's 38 tests, ported (its fixture bank and requirements)
  2. one regression per documented fix, D-1 to D-10, plus D1/D2/D5/D6/D9
  3. the surfaces the specification lists as untested (§6.4)
  4. fixes found by running the sample people (CN-11 to CN-14)
  5. the adversarial fixture matrix (3 announcements x 4 evidence banks)
  6. the ADA metamorphic test (CB-01) and the fact-level allowlist (CB-02)
"""
import dataclasses
import datetime as dt
import inspect
import itertools
import unittest

from app.domains.career import analysis as an
from app.domains.career import documents as docs
from app.domains.career.enforcement import (
    NEEDS_VERIFICATION, NEVER_GRANTABLE, OUTBOUND_OK, AuditLog, ConsentBroker, ConsentError, ConsentGrant,
    DocumentAssembler, EvidenceBank, EvidenceError, EvidenceItem, FabricationGuard, Metric, ProtectedFieldGuard,
    Statement, Verification, assert_no_hiring_guarantee, numbers_in, strip_structural)
from app.domains.career.samples import bank_for, item_from, load_samples

V = Verification
TODAY = dt.date(2026, 10, 29)
SAMPLES = load_samples()


def spec_bank(audit=None):
    """The specification's three-item matrix: doc-backed, attested, unverified."""
    audit = audit or AuditLog()
    return EvidenceBank(audit, [
        EvidenceItem("ev_army_platoon_sgt", "military_experience", "Platoon Sergeant",
                     "Supervised a platoon of soldiers and maintained a vehicle fleet. Led convoy operations and "
                     "trained junior leaders.", V.DOCUMENT_BACKED,
                     (Metric("31", "soldiers supervised", "NCOER 2021-06", V.DOCUMENT_BACKED),
                      Metric("$4.2 million", "fleet value", "property book", V.DOCUMENT_BACKED)),
                     start_date="2016-04", end_date="2022-09", hours_per_week=40,
                     skills=("supervision", "fleet maintenance", "training")),
        EvidenceItem("ev_warehouse_lead", "civilian_experience", "Warehouse Lead",
                     "Led a shift of associates in a distribution center using a WMS. Supervised receiving and "
                     "shipping.", V.USER_ATTESTED, (Metric("12", "associates", "user statement", V.USER_ATTESTED),),
                     start_date="2022-10", hours_per_week=40, skills=("WMS", "inventory", "supervision")),
        EvidenceItem("ev_unverified_sixsigma", "credential", "Six Sigma Green Belt",
                     "Six Sigma Green Belt certification.", V.UNVERIFIED),
    ]), audit


def spec_reqs():
    def req(rid, text, kind, cat, legal=False):
        return an.JobRequirement(rid, text, kind, cat, tuple(an.keywords_from(text)), legal)
    return [req("r1", "Experience supervising teams and fleet operations", an.ReqKind.REQUIRED, "experience"),
            req("r2", "Proficiency with WMS inventory systems", an.ReqKind.REQUIRED, "skill"),
            req("r3", "Commercial driver's license Class A", an.ReqKind.REQUIRED, "credential", True),
            req("r4", "Six Sigma certification", an.ReqKind.PREFERRED, "credential")]


def check(text, *ids, bank=None, **kw):
    bank = bank or spec_bank()[0]
    return [f.problem for f in FabricationGuard(bank).check(Statement(text, tuple(ids), **kw))]


def grant(**kw):
    base = dict(user_id="u1", tenant_id="t1", source_module="vetbuddy", purpose="resume_generation",
                allowed_fields=frozenset({"service_history", "duty_titles"}), granted_on=TODAY - dt.timedelta(days=10))
    base.update(kw)
    return ConsentGrant(**base)


def read(broker, **kw):
    base = dict(user_id="u1", tenant_id="t1", source="vetbuddy", purpose="resume_generation",
                requested_fields=["service_history", "duty_titles", "va_disability_rating", "home_address"],
                payload={"service_history": "Army 2016-2022", "duty_titles": ["Platoon Sergeant"],
                         "va_disability_rating": 70, "home_address": "123 Example St"},
                requesting_agent="career_resume_agent", when=TODAY)
    base.update(kw)
    return broker.read(**base)


# ── 1. the specification's tests ─────────────────────────────────────────────

class Consent(unittest.TestCase):
    def test_wellness_cannot_be_granted_at_all(self):
        b = ConsentBroker(AuditLog())
        with self.assertRaises(ConsentError):
            b.grant(grant(source_module="wellness_checkin", purpose=None, allowed_fields=frozenset({"x"})))

    def test_read_returns_only_granted_fields(self):
        b = ConsentBroker(AuditLog())
        b.grant(grant())
        out = read(b)
        self.assertEqual(set(out), {"service_history", "duty_titles"})

    def test_purpose_mismatch_denies_read(self):
        b = ConsentBroker(AuditLog())
        b.grant(grant())
        with self.assertRaises(ConsentError):
            read(b, purpose="employer_disclosure")

    def test_expired_grant_denies_read(self):
        b = ConsentBroker(AuditLog())
        b.grant(grant(expires_on=TODAY - dt.timedelta(days=1)))
        with self.assertRaises(ConsentError):
            read(b)

    def test_revocation_takes_effect(self):
        b = ConsentBroker(AuditLog())
        b.grant(grant())
        self.assertEqual(b.revoke("u1", "vetbuddy"), 1)
        with self.assertRaises(ConsentError):
            read(b)


class Fabrication(unittest.TestCase):
    def test_statement_without_provenance_is_held(self):
        self.assertEqual(check("Led convoy operations."), ["no_provenance"])

    def test_unverified_evidence_cannot_be_cited(self):
        self.assertEqual(check("Six Sigma Green Belt.", "ev_unverified_sixsigma"), ["unverified_evidence"])

    def test_verified_metric_passes(self):
        self.assertEqual(check("Supervised 31 soldiers.", "ev_army_platoon_sgt"), [])

    def test_inflated_metric_is_caught(self):
        self.assertEqual(check("Supervised 35 soldiers.", "ev_army_platoon_sgt"), ["untraceable_metric"])

    def test_invented_percentage_is_caught(self):
        self.assertEqual(check("Improved fleet readiness by 23%.", "ev_army_platoon_sgt"), ["untraceable_metric"])

    def test_nonnumeric_restatement_passes(self):
        self.assertEqual(check("Improved fleet readiness.", "ev_army_platoon_sgt"), [])

    def test_idiom_24_7_is_not_read_as_a_metric(self):
        self.assertEqual(check("Ran 24/7 convoy operations.", "ev_army_platoon_sgt"), [])

    def test_pay_grade_is_not_read_as_a_metric(self):
        self.assertEqual(check("Served as an E-7 platoon sergeant.", "ev_army_platoon_sgt"), [])

    def test_year_is_not_read_as_a_metric(self):
        self.assertEqual(check("Promoted in 2018.", "ev_army_platoon_sgt"), [])

    def test_dollar_metric_with_formatting_passes(self):
        self.assertEqual(check("Maintained a $4.2 million fleet.", "ev_army_platoon_sgt"), [])

    def test_metrics_do_not_leak_across_evidence_items(self):
        self.assertEqual(check("Supervised 31 associates.", "ev_warehouse_lead"), ["untraceable_metric"])


class Protected(unittest.TestCase):
    CASES = [("SSN 123-45-6789", "social security number"),
             ("70% service-connected disabled veteran", "va disability rating"),
             ("Rated 100% permanent and total", "permanent and total rating"),
             ("Date of birth: 1985", "full date of birth"),
             ("Married, two children", "marital status"),
             ("Manages PTSD with support", "medical diagnosis")]

    def test_protected_content_detected(self):
        for text, field in self.CASES:
            with self.subTest(text=text):
                self.assertIn(field, [f.field_name for f in ProtectedFieldGuard().scan(text)])

    def test_clean_resume_text_has_no_protected_findings(self):
        self.assertEqual(ProtectedFieldGuard().scan(
            "Supervised a platoon of 31 soldiers and maintained a $4.2 million vehicle fleet. Led convoy operations "
            "across three states and served as the single point of contact for maintenance."), [])


class Assembly(unittest.TestCase):
    def test_assembler_holds_bad_statements_and_keeps_good_ones(self):
        bank, audit = spec_bank()
        r = DocumentAssembler(bank, audit).assemble(
            [Statement("Supervised 31 soldiers.", ("ev_army_platoon_sgt",)), Statement("Cut costs by 40%.", ("ev_warehouse_lead",)),
             Statement("Led operations.", ())], document_id="d1", actor="u1")
        self.assertEqual((len(r.accepted), len(r.held), r.voided), (1, 2, False))

    def test_protected_content_voids_whole_document(self):
        bank, audit = spec_bank()
        r = DocumentAssembler(bank, audit).assemble(
            [Statement("Supervised 31 soldiers.", ("ev_army_platoon_sgt",)),
             Statement("70% service-connected disabled veteran.", ("ev_army_platoon_sgt",))], document_id="d1", actor="u1")
        self.assertEqual(r.accepted, ())
        self.assertTrue(r.voided and r.protected_findings)
        collateral = [h for h in r.held if not h.findings]
        self.assertEqual([h.statement.text for h in collateral], ["Supervised 31 soldiers."])

    def test_assembly_writes_audit_events(self):
        bank, audit = spec_bank()
        before = len(audit)
        DocumentAssembler(bank, audit).assemble([Statement("Supervised 31 soldiers.", ("ev_army_platoon_sgt",))],
                                               document_id="d1", actor="u1")
        self.assertEqual(len(audit), before + 1)
        self.assertEqual(audit.events[-1].action, "document.assembled")


class MatrixAndCompetitiveness(unittest.TestCase):
    def setUp(self):
        self.bank, _ = spec_bank()
        self.rows = {r.requirement.requirement_id: r for r in an.build_matrix(spec_reqs(), self.bank)}

    def test_matrix_marks_missing_legal_credential_as_none(self):
        r3 = self.rows["r3"]
        self.assertIs(r3.strength, an.Strength.NONE)
        self.assertTrue(r3.blocking)
        self.assertIn("can't substitute", r3.action)

    def test_matrix_does_not_count_unverified_credential_as_met(self):
        r4 = self.rows["r4"]
        self.assertIs(r4.strength, an.Strength.WEAK)
        self.assertTrue(r4.needs_confirmation)
        self.assertEqual(r4.evidence_ids, ())

    def test_matrix_finds_supervision_evidence(self):
        r1 = self.rows["r1"]
        self.assertIn(r1.strength, an.SUPPORTED)
        self.assertIn("ev_army_platoon_sgt", r1.evidence_ids)

    def test_competitiveness_returns_no_composite_number(self):
        for c in an.competitiveness(list(self.rows.values()), self.bank):
            self.assertFalse(c.label.replace(".", "").isdigit())
            self.assertIn(c.label, an.STATUS_LABELS)

    def test_blocking_legal_credential_drives_significant_gap(self):
        labels = {c.category: c.label for c in an.competitiveness(list(self.rows.values()), self.bank)}
        self.assertEqual(labels["credential"], "Significant qualifications gap")


class HiringGuarantees(unittest.TestCase):
    def test_hiring_guarantees_rejected(self):
        for text in ("This resume guarantees an interview.", "You will be hired.", "You are certain to get the job."):
            with self.subTest(text=text), self.assertRaises(ValueError):
                assert_no_hiring_guarantee(text)

    def test_calibrated_language_allowed(self):
        assert_no_hiring_guarantee("Your experience is a reasonable match for the posted requirements.")

    def test_the_gate_holds_a_guarantee(self):
        self.assertIn("prohibited_assurance", check("Guaranteed results: supervised 31 soldiers.", "ev_army_platoon_sgt"))


class Regressions(unittest.TestCase):
    def test_regression_hours_per_week_does_not_license_a_metric(self):          # D-1
        self.assertEqual(check("Cut costs by 40%.", "ev_army_platoon_sgt"), ["untraceable_metric"])

    def test_regression_hours_per_week_still_allowed_in_federal_format(self):    # D-1 guard rail
        self.assertEqual(check("Platoon Sergeant, 40 hours per week.", "ev_army_platoon_sgt"), [])

    def test_regression_protected_content_reported_as_protected_not_as_metric(self):   # D-2
        bank, audit = spec_bank()
        r = DocumentAssembler(bank, audit).assemble([Statement("70% service-connected disabled.", ("ev_army_platoon_sgt",))],
                                                    document_id="d", actor="u")
        problems = [f.problem for h in r.held for f in h.findings]
        self.assertIn("protected_content", problems)
        self.assertNotIn("untraceable_metric", problems)


# ── 2. fixes D-3 to D-10 and the JS-side corrections ─────────────────────────

def home(pid):
    """A sample person's own announcement, matrix and bank."""
    p = SAMPLES[pid]
    audit = AuditLog()
    bank = bank_for(p, audit)
    reqs = an.extract_requirements(p["announcement"]["raw"])
    return p, bank, reqs, an.build_matrix(reqs, bank), audit


def row_with(rows, fragment):
    return next(r for r in rows if fragment.lower() in r.requirement.text.lower())


class DocumentedFixes(unittest.TestCase):
    def test_d3_generic_qualifier_does_not_match_a_licence(self):
        _, _, _, rows, _ = home("jordan")
        lic = row_with(rows, "unencumbered")
        self.assertNotIn("ev_j_bls", lic.evidence_ids + lic.unverified_ids)      # the card that says "Current."
        self.assertNotIn("current", lic.requirement.keywords)

    def test_d4_absence_is_never_support(self):
        _, bank, _, rows, _ = home("jordan")
        lic = row_with(rows, "unencumbered")
        self.assertEqual(lic.absence_ids, ("ev_j_lic",))
        self.assertNotIn("ev_j_lic", lic.evidence_ids + lic.unverified_ids)
        self.assertIn("documents its absence", lic.gap)
        with self.assertRaises(EvidenceError):
            bank.verify("ev_j_lic", V.USER_ATTESTED, "jordan")

    def test_d5_legal_credential_with_weak_support_blocks(self):
        _, _, _, rows, _ = home("dana")
        cdl = row_with(rows, "commercial driver")
        self.assertIs(cdl.strength, an.Strength.WEAK)
        self.assertTrue(cdl.blocking)

    def test_d6_required_documents_is_not_a_qualification(self):
        for pid in ("dana", "marcus"):
            _, _, reqs, _, _ = home(pid)
            self.assertFalse([r for r in reqs if "DD-214" in r.text], pid)

    def test_d7_wrapped_prose_requirement_is_joined(self):
        _, _, reqs, _, _ = home("marcus")
        spec = next(r for r in reqs if r.text.startswith("One year of specialized experience"))
        self.assertIn("STIGs to networked systems", spec.text)                  # three source lines, one requirement

    def test_d8_hyphenated_and_possessive_terms_match(self):
        _, _, _, rows, _ = home("jordan")
        self.assertIn("ev_j_rn", row_with(rows, "medical-surgical").evidence_ids)
        self.assertIn("ev_j_adn", row_with(rows, "associate's degree").evidence_ids)

    def test_d9_acronyms_are_not_stemmed(self):
        for word in ("bls", "acls", "wms", "adn", "bsn"):
            self.assertEqual(an.stem(word), word)
        self.assertEqual(an.stem("supervising"), an.stem("supervised"))

    def test_d10_quoted_requirement_is_not_a_claim(self):
        text = "You asked for 3+ years supervising a team of 10 or more. Led convoy operations."
        quoted = "3+ years supervising a team of 10 or more"
        self.assertEqual(check(text, "ev_army_platoon_sgt", quoted=quoted), [])
        self.assertEqual(check(text, "ev_army_platoon_sgt"), ["untraceable_metric", "untraceable_metric"])

    def test_js_d1_all_moderate_is_competitive(self):
        self.assertEqual(an.label_for([an.Strength.MODERATE] * 3, False), "Competitive with minor gaps")

    def test_js_d2_whole_tokens_and_titles(self):
        audit = AuditLog()
        bank = EvidenceBank(audit, [EvidenceItem("q", "military_experience", "Quartermaster", "Managed supply.", V.USER_ATTESTED)])
        art = an.JobRequirement("r", "Art direction", an.ReqKind.REQUIRED, "skill", ("art",))
        self.assertIs(an.build_matrix([art], bank)[0].strength, an.Strength.NONE)
        qm = an.JobRequirement("r", "Quartermaster experience", an.ReqKind.REQUIRED, "experience",
                               tuple(an.keywords_from("Quartermaster")))
        self.assertEqual(an.build_matrix([qm], bank)[0].evidence_ids, ("q",))  # title is in the haystack

    def test_js_d5_series_grade_is_not_a_claim(self):
        self.assertEqual(numbers_in(strip_structural("Applying for GS-2210-11 and GS-09 roles.")), set())

    def test_js_d6_single_and_therapy(self):
        names = lambda t: [f.field_name for f in ProtectedFieldGuard().scan(t)]
        self.assertEqual(names("Single point of contact for the motor pool."), [])
        self.assertEqual(names("Attends therapy weekly."), ["medical diagnosis"])


# ── 3. surfaces the specification lists as untested ──────────────────────────

class UntestedSurfaces(unittest.TestCase):
    def test_duplicate_evidence_is_refused_not_overwritten(self):
        bank, _ = spec_bank()
        with self.assertRaises(EvidenceError):
            bank.add(EvidenceItem("ev_warehouse_lead", "credential", "x", "y"))

    def test_verify_unknown_id_and_downgrade(self):
        bank, audit = spec_bank()
        with self.assertRaises(EvidenceError):
            bank.verify("nope", V.USER_ATTESTED, "u1")
        bank.verify("ev_warehouse_lead", V.UNVERIFIED, "u1")
        self.assertEqual(audit.events[-1].previous_value, "user_attested")
        self.assertEqual(check("Led a shift of 12 associates.", "ev_warehouse_lead", bank=bank), ["unverified_evidence"])

    def test_attesting_a_record_does_not_license_its_unconfirmed_figures(self):
        audit = AuditLog()
        bank = EvidenceBank(audit, [EvidenceItem("x", "accomplishment", "Award", "Saved costs.", V.UNVERIFIED,
                                                 (Metric("40", "percent saved", "user", V.UNVERIFIED),))])
        bank.verify("x", V.USER_ATTESTED, "u1")
        self.assertEqual(check("Saved 40% in costs.", "x", bank=bank), ["untraceable_metric"])

    def test_future_dated_grant_is_inactive(self):
        b = ConsentBroker(AuditLog())
        b.grant(grant(granted_on=TODAY + dt.timedelta(days=1)))
        with self.assertRaises(ConsentError):
            read(b)

    def test_tenant_isolation(self):
        b = ConsentBroker(AuditLog())
        b.grant(grant(tenant_id="t1"))
        with self.assertRaises(ConsentError):
            read(b, tenant_id="t2")

    def test_revoke_is_broad(self):
        b = ConsentBroker(AuditLog())
        b.grant(grant(tenant_id="t1"))
        b.grant(grant(tenant_id="t2"))
        self.assertEqual(b.revoke("u1", "vetbuddy"), 2)

    def test_every_structural_pattern(self):
        for text in ("GS-11", "2024-05-01", "Title 10", "Title 32", "05/2019", "2016-2022", "2016 – 2022",
                     "SY0-701", "Class A", "88M", "25B", "3D0X2", "IT1", "40 hours per week"):
            with self.subTest(text=text):
                self.assertEqual(numbers_in(strip_structural(f"Held {text}.")), set())

    def test_every_protected_detector(self):
        for text, field in (("Religion: none listed", "religion"), ("Race: not stated", "race or ethnicity"),
                            ("Disability rating of 70%", "va disability rating"),
                            ("Salary target $85,000", "salary target")):
            with self.subTest(text=text):
                self.assertIn(field, [f.field_name for f in ProtectedFieldGuard().scan(text)])

    def test_insufficient_information(self):
        self.assertEqual(an.label_for([], False), "Insufficient information")

    def test_multi_citation_union_and_mixed_provenance(self):
        self.assertEqual(check("Led 31 soldiers, then 12 associates.", "ev_army_platoon_sgt", "ev_warehouse_lead"), [])
        self.assertEqual(check("Led 31 soldiers and 50 riggers.", "ev_army_platoon_sgt", "ev_missing"),
                         ["unknown_evidence", "untraceable_metric"])

    def test_audit_is_closed_and_immutable_and_refusals_are_recorded(self):
        audit = AuditLog()
        with self.assertRaises(ValueError):
            audit.record("consent.grnted", "x", "typo")
        b = ConsentBroker(audit)
        with self.assertRaises(ConsentError):
            b.grant(grant(source_module="wellness_checkin", purpose=None, allowed_fields=frozenset({"x"})))
        e = audit.events[-1]
        self.assertEqual(e.action, "consent.grant.refused")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            e.reason = "edited"
        self.assertEqual(len(e.event_id), 36)
        self.assertTrue(e.occurred_at.endswith("+00:00"))

    def test_no_provenance_exemption_lives_in_the_gate_and_refuses_numbers(self):
        self.assertEqual(check("I am applying for this position.", no_provenance_ok=True), [])
        self.assertEqual(check("I bring 12 years of leadership.", no_provenance_ok=True), ["no_provenance"])

    def test_sensitive_needs_a_per_document_opt_in(self):
        audit = AuditLog()
        bank = EvidenceBank(audit, [EvidenceItem("s", "credential", "Secret clearance", "Active Secret clearance.",
                                                 V.DOCUMENT_BACKED, sensitive=True)])
        guard = FabricationGuard(bank)
        self.assertEqual([f.problem for f in guard.check(Statement("Secret clearance.", ("s",)))], ["sensitive_not_opted_in"])
        self.assertEqual(guard.check(Statement("Secret clearance.", ("s",)), sensitive_opt_in=frozenset({"s"})), [])


# ── 4. fixes found by running the sample people ──────────────────────────────

class SampleFindings(unittest.TestCase):
    def test_cn11_empty_bank_is_insufficient_information_not_a_gap(self):
        audit = AuditLog()
        empty = EvidenceBank(audit)
        reqs = an.extract_requirements(SAMPLES["jordan"]["announcement"]["raw"])
        labels = {c.label for c in an.competitiveness(an.build_matrix(reqs, empty), empty)}
        self.assertEqual(labels, {"Insufficient information"})

    def test_cn12_held_but_unverified_licence_says_verify(self):
        _, _, _, rows, _ = home("dana")
        cdl = row_with(rows, "commercial driver")
        self.assertTrue(cdl.needs_confirmation)
        self.assertIn("isn't verified yet", cdl.action)

    def test_cn13_licence_support_comes_only_from_a_credential_record(self):
        _, _, _, rows, _ = home("dana")
        cdl = row_with(rows, "commercial driver")
        self.assertNotIn("ev_d_dispatch", cdl.evidence_ids + cdl.unverified_ids)   # "drivers" in a dispatch job

    def test_cn13_absence_speaks_only_to_its_own_kind_of_requirement(self):
        _, _, _, rows, _ = home("marcus")
        self.assertEqual(row_with(rows, "specialized experience").absence_ids, ())
        clearance = row_with(rows, "clearance")
        self.assertEqual(clearance.absence_ids, ("ev_m_clear",))
        self.assertIn("doesn't assess eligibility", clearance.action)

    def test_cn14_letters_disclose_only_documented_legal_gaps(self):
        letters = {}
        for pid in ("dana", "marcus", "jordan"):
            p, bank, _, rows, audit = home(pid)
            doc = docs.generate_cover_letter(p["announcement"]["title"], p["announcement"]["employer"], rows, bank,
                                             audit, actor=pid)
            letters[pid] = " ".join(s.text for s in doc.result.accepted)
        self.assertIn("do not currently meet", letters["jordan"])                     # documented absence of a licence
        self.assertNotIn("do not currently meet", letters["dana"])                    # diploma unrecorded; CDL unverified
        self.assertNotIn("do not currently meet", letters["marcus"])                  # clearance status unknown

    def test_military_codes_are_not_claims(self):
        for pid in ("dana", "marcus"):
            p, bank, reqs, _, audit = home(pid)
            doc = docs.generate_resume("federal", docs.Person(pid, p["objective"]), reqs, bank, audit, actor=pid)
            self.assertEqual([h.statement.text for h in doc.result.held], [], pid)


# ── 5. adversarial fixture matrix ────────────────────────────────────────────

BANKS = ("dana", "marcus", "jordan", "empty")
ANNOUNCEMENTS = ("dana", "marcus", "jordan")
EXTRACTED = {"dana": (5, 2), "marcus": (3, 1), "jordan": (4, 3)}          # (required, preferred), pinned
BLOCKING_HOME = {"dana": ["r2"], "marcus": [], "jordan": ["r1"]}


def bank_named(name, audit):
    return EvidenceBank(audit) if name == "empty" else bank_for(SAMPLES[name], audit)


class FixtureMatrix(unittest.TestCase):
    def test_extraction_counts(self):
        for pid, (req, pref) in EXTRACTED.items():
            reqs = an.extract_requirements(SAMPLES[pid]["announcement"]["raw"])
            self.assertEqual((sum(r.kind is an.ReqKind.REQUIRED for r in reqs),
                              sum(r.kind is an.ReqKind.PREFERRED for r in reqs)), (req, pref), pid)

    def test_blocking_on_home_announcements(self):
        for pid, expected in BLOCKING_HOME.items():
            _, _, _, rows, _ = home(pid)
            self.assertEqual([r.requirement.requirement_id for r in rows if r.blocking], expected, pid)

    def test_invariants_across_every_pair(self):
        for ann, bname in itertools.product(ANNOUNCEMENTS, BANKS):
            with self.subTest(announcement=ann, bank=bname):
                audit = AuditLog()
                bank = bank_named(bname, audit)
                reqs = an.extract_requirements(SAMPLES[ann]["announcement"]["raw"])
                rows = an.build_matrix(reqs, bank)
                for r in rows:
                    self.assertFalse(r.blocking and not r.requirement.legally_required)
                    self.assertFalse(set(r.absence_ids) & set(r.evidence_ids + r.unverified_ids))
                    for eid in r.evidence_ids:
                        self.assertTrue(bank.get(eid).outbound)
                    if r.strength is an.Strength.NONE:
                        self.assertTrue(r.gap and r.action)
                for c in an.competitiveness(rows, bank):
                    self.assertIn(c.label, an.STATUS_LABELS)
                p = SAMPLES.get(bname, {"objective": "Sample objective"})
                for rtype in docs.RESUME_TYPES:
                    doc = docs.generate_resume(rtype, docs.Person(bname, p["objective"]), reqs, bank, audit,
                                               actor=bname, demonstrate_gate=True)
                    guard = FabricationGuard(bank)
                    for s in doc.result.accepted:                         # nothing accepted would fail a re-check
                        self.assertEqual(guard.check(s), [], s.text)
                        for eid in s.evidence_ids:
                            self.assertTrue(bank.get(eid).outbound and not bank.get(eid).negative)

    def test_the_gate_catches_the_naive_impact_line(self):
        for pid in ("dana", "marcus"):
            p, bank, reqs, _, audit = home(pid)
            doc = docs.generate_resume("ats", docs.Person(pid, p["objective"]), reqs, bank, audit, actor=pid,
                                       demonstrate_gate=True)
            held = {h.statement.text: [f.problem for f in h.findings] for h in doc.result.held}
            self.assertEqual(held, {docs.NAIVE_IMPACT: ["untraceable_metric", "untraceable_metric"]}, pid)

    def test_star_never_invents_a_result(self):
        for pid in ("dana", "marcus", "jordan"):
            _, bank, _, _, _ = home(pid)
            for story in docs.generate_star(bank):
                if story.result is None:
                    self.assertFalse(story.complete)


# ── 6. ADA metamorphic test (CB-01) and fact-level allowlist (CB-02) ─────────

HEALTH_VARIANTS = [f"Rated {n}% service-connected disabled." for n in range(0, 101, 10)] + [
    "VA disability rating of 70%.", "Rated 100% permanent and total.", "Manages PTSD with weekly therapy.",
    "Diagnosed with TBI in 2019.", "Prescribed medication for sleep.", "Married with two children.",
    "Religion: Baptist.", "Race: Black.", "Date of birth: 1984."]


def with_health(person, sentence):
    """The same person with a health-derived (or protected-class) fact written into every record."""
    q = {**person, "evidence": [{**e, "summary": e["summary"] + " " + sentence,
                                 "title": e["title"] + ", " + sentence} for e in person["evidence"]]}
    return q


def matrix_signature(rows):
    return [(r.requirement.requirement_id, r.strength, r.blocking, r.gap, r.action, r.evidence_ids,
             r.unverified_ids, r.absence_ids, r.needs_confirmation) for r in rows]


class ADAMetamorphic(unittest.TestCase):
    """For any profile and any value of a health-derived fact, career output must not change.
    Output here means every finding and recommendation: the matrix, the category labels and the
    tailoring order. (Documents still hold a protected line in place, by design: that is the
    non-disclosure guarantee, not a change in what the system recommends.)"""

    def test_matrix_labels_and_tailoring_are_invariant(self):
        for ann, pid in itertools.product(ANNOUNCEMENTS, ("dana", "marcus", "jordan")):
            reqs = an.extract_requirements(SAMPLES[ann]["announcement"]["raw"])
            base_bank = bank_for(SAMPLES[pid], AuditLog())
            base_rows = an.build_matrix(reqs, base_bank)
            base = (matrix_signature(base_rows),
                    [(c.category, c.label, c.basis) for c in an.competitiveness(base_rows, base_bank)],
                    sorted((an.relevance(i, reqs), i.evidence_id) for i in base_bank.all()))
            for sentence in HEALTH_VARIANTS:
                with self.subTest(announcement=ann, person=pid, fact=sentence):
                    bank = bank_for(with_health(SAMPLES[pid], sentence), AuditLog())
                    rows = an.build_matrix(reqs, bank)
                    got = (matrix_signature(rows),
                           [(c.category, c.label, c.basis) for c in an.competitiveness(rows, bank)],
                           sorted((an.relevance(i, reqs), i.evidence_id) for i in bank.all()))
                    self.assertEqual(got, base)

    def test_health_content_never_becomes_a_keyword(self):
        for sentence in HEALTH_VARIANTS:
            with self.subTest(fact=sentence):
                self.assertEqual(an.haystack(sentence).split(), [w for w in an.haystack(sentence).split()
                                                                 if not any(k in w for k in ("ptsd", "tbi", "disab"))])
                req = an.JobRequirement("r", "Experience", an.ReqKind.REQUIRED, "experience",
                                        tuple(an.keywords_from("PTSD TBI disabled therapy married")))
                bank = EvidenceBank(AuditLog(), [EvidenceItem("x", "military_experience", "Role", sentence, V.USER_ATTESTED)])
                self.assertIs(an.build_matrix([req], bank)[0].strength, an.Strength.NONE)

    def test_no_engine_entry_point_accepts_a_health_fact(self):
        for fn in (an.extract_requirements, an.build_matrix, an.competitiveness, an.relevance, docs.generate_resume,
                   docs.generate_cover_letter, docs.generate_star):
            params = set(inspect.signature(fn).parameters)
            self.assertFalse(params & NEVER_GRANTABLE, fn.__name__)

    def test_cb02_health_fields_can_never_be_granted_or_read(self):
        b = ConsentBroker(AuditLog())
        for field in sorted(NEVER_GRANTABLE):
            with self.subTest(field=field), self.assertRaises(ConsentError):
                b.grant(grant(allowed_fields=frozenset({"service_history", field})))
        with self.assertRaises(ConsentError):                                         # not on the module's allowlist
            b.grant(grant(allowed_fields=frozenset({"home_address"})))
        b.grant(grant())
        out = read(b, requested_fields=["service_history", *sorted(NEVER_GRANTABLE)],
                   payload={"service_history": "x", **{f: 1 for f in NEVER_GRANTABLE}})
        self.assertEqual(set(out), {"service_history"})

    def test_cb02_every_catalog_field_is_grantable_and_none_is_health(self):
        from app.domains.career.enforcement import CATALOG
        for mid, entry in CATALOG.items():
            self.assertFalse(set(entry["fields"]) & NEVER_GRANTABLE, mid)


class Redaction(unittest.TestCase):
    def test_the_protected_clause_goes_with_its_value(self):
        from app.domains.career.enforcement import redact_protected
        self.assertEqual(redact_protected("Race: Black. Led convoys, rated 70% service-connected disabled, trained crews."),
                         "Led convoys, trained crews.")
        self.assertEqual(redact_protected("Manages PTSD with weekly therapy."), "")
