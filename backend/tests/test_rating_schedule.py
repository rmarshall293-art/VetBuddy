"""38 CFR Part 4 rating schedule as reference data (migration 0015).

The schedule explains how VA describes criteria. It is never matched against
a veteran's symptoms (governance section 5), so the tests prove there is no
symptom column, no symptom search, and nothing VERIFIED without a reviewer.
"""
import copy
import json
import unittest

from app.domains.reference import corpus
from app.infra.db import DatabaseError, connect

from tests.support import ADMIN_DSN, APP_DSN, ApiCase

C = corpus.build()


class Shape(unittest.TestCase):
    def test_737_codes_and_their_criteria(self):
        codes = C.tables["rating_code"]
        self.assertEqual(len(codes), 737)
        self.assertEqual(len({r["code"] for r in codes}), 737)
        self.assertEqual(sum(r["has_criteria"] for r in codes), 364)
        self.assertGreater(len(C.tables["rating_criterion"]), 700)

    def test_statuses(self):
        by = {}
        for r in C.tables["rating_code"]:
            by[r["status"]] = by.get(r["status"], 0) + 1
        self.assertEqual(by, {"UNVERIFIED": 686, "SUPERSEDED": 51})
        self.assertTrue(all(r["status"] == "SUPERSEDED" for r in C.tables["rating_code"]
                            if r["body_system"] == "THE DIGESTIVE SYSTEM"))

    def test_known_names_and_no_invented_codes(self):
        by = {r["code"]: r["name"] for r in C.tables["rating_code"]}
        self.assertEqual(by["6847"], "Sleep Apnea Syndromes")
        self.assertEqual(by["9411"], "Posttraumatic stress disorder")
        for invented in ("9420", "9999", "8110", "6814", "6848", "6399"):  # from the rejected va_claims_data.json
            self.assertNotIn(invented, by)

    def test_no_pdf_page_headers_in_names(self):
        self.assertFalse([r["code"] for r in C.tables["rating_code"] if "Pt. 4" in r["name"] or "Department of" in r["name"]])

    def test_no_symptom_columns_anywhere(self):
        for table in ("rating_code", "rating_criterion"):
            for r in C.tables[table]:
                self.assertFalse({"keywords", "symptoms"} & set(r), table)


class ValidatorRejects(unittest.TestCase):
    def test_symptom_keywords_refused_at_load(self):
        raw = json.loads((corpus.DATA / "rating_schedule.json").read_text())
        raw["codes"][0]["keywords"] = ["back pain"]
        orig = corpus._read
        try:
            corpus._read = lambda name: (raw, "0" * 64) if name == "rating_schedule" else orig(name)
            with self.assertRaises(corpus.CorpusError) as ctx:
                corpus.build()
        finally:
            corpus._read = orig
        self.assertIn("symptom keywords are prohibited", str(ctx.exception))

    def mutate(self, fn):
        c = copy.deepcopy(C)
        fn(c.tables)
        with self.assertRaises(corpus.CorpusError) as ctx:
            corpus.validate(c)
        return str(ctx.exception)

    def test_verified_without_reviewer(self):
        self.assertIn("VERIFIED without a named reviewer",
                      self.mutate(lambda t: t["rating_code"][0].update(status="VERIFIED")))

    def test_bad_percent(self):
        self.assertIn("steps of 10", self.mutate(lambda t: t["rating_criterion"][0].update(percent=15)))

    def test_orphan_criterion(self):
        self.assertIn("unknown code", self.mutate(lambda t: t["rating_criterion"][0].update(code="0000")))


class Database(unittest.TestCase):
    def test_loaded_and_read_only_for_app(self):
        with connect(APP_DSN) as conn:
            n = conn.one("SELECT count(*) AS n FROM ref.rating_code")["n"]
            self.assertEqual(n, 737)
            with self.assertRaises(DatabaseError):
                conn.query("UPDATE ref.rating_code SET status = 'VERIFIED' WHERE code = '6847'")

    def test_db_refuses_verified_without_reviewer_even_for_owner(self):
        with connect(ADMIN_DSN) as conn:
            with self.assertRaises(DatabaseError):
                conn.query("UPDATE ref.rating_code SET status = 'VERIFIED' WHERE code = '6847'")

    def test_db_refuses_bad_percent(self):
        with connect(ADMIN_DSN) as conn:
            with self.assertRaises(DatabaseError):
                conn.query("INSERT INTO ref.rating_criterion (criterion_id, code, position, percent, criteria_text) "
                             "VALUES ('6847:99', '6847', 99, 15, 'x')")


class Api(ApiCase):
    def test_index_has_no_symptom_search(self):
        j = self.client.get("/api/v1/reference/rating-schedule?body_system=THE%20EAR").json()
        self.assertEqual({r["body_system"] for r in j["codes"]}, {"THE EAR"})
        self.assertIn("not an assessment of your condition", j["label"])
        self.assertIn("accredited", j["vso_referral"])
        self.assertNotIn("criteria", j["codes"][0])
        self.assertEqual(len(self.client.get("/api/v1/reference/rating-schedule?q=back%20pain").json()["codes"]), 737)

    def test_code_detail(self):
        j = self.client.get("/api/v1/reference/rating-schedule/6847").json()
        self.assertEqual(j["code"]["name"], "Sleep Apnea Syndromes")
        self.assertEqual(j["code"]["status"], "UNVERIFIED")
        self.assertEqual(max(c["percent"] for c in j["criteria"]), 100)

    def test_unknown_code_is_404(self):
        r = self.client.get("/api/v1/reference/rating-schedule/9999")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["error"]["code"], "UNKNOWN_RATING_CODE")


if __name__ == "__main__":
    unittest.main()
