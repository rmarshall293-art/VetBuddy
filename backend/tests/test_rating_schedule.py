"""38 CFR Part 4 rating schedule as reference data (migrations 0017, 0018).

The schedule explains how VA describes criteria. It is never matched against
a veteran's symptoms (governance section 5), so the tests prove there is no
symptom column, no symptom search, and nothing VERIFIED without a reviewer.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

from app.domains.reference import corpus
from app.infra.db import DatabaseError, connect

from tests.support import ADMIN_DSN, APP_DSN, ApiCase

C = corpus.build()
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import rebuild_rating_criteria as rebuild  # noqa: E402

BY_CODE = {c["code"]: c for c in json.loads((corpus.DATA / "rating_schedule.json").read_text())["codes"]}


def rows(code):
    return [(k["percent"], k.get("percent_minor")) for k in BY_CODE[code]["criteria"]]


class Shape(unittest.TestCase):
    def test_737_codes_and_their_criteria(self):
        codes = C.tables["rating_code"]
        self.assertEqual(len(codes), 737)
        self.assertEqual(len({r["code"] for r in codes}), 737)
        self.assertEqual(sum(r["has_criteria"] for r in codes), 383)
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


class TranscriptionDamage(unittest.TestCase):
    """The 2020 PDF parse had one percent column and leaked page headers. These pin the repair
    (scripts/rebuild_rating_criteria.py, eCFR snapshot amended through 2026-08-27)."""

    def test_no_row_shows_pdf_parse_damage(self):
        bad = [(c["code"], k["text"][-60:]) for c in BY_CODE.values() for k in c["criteria"] if rebuild.DAMAGE.search(k["text"])]
        self.assertEqual(bad, [])

    def test_dataset_matches_the_ecfr_snapshot(self):
        data = json.loads((corpus.DATA / "rating_schedule.json").read_text())
        tables = rebuild.parse_tables(sorted(rebuild.SNAP_DIR.glob("38cfr_*.xml")))
        self.assertEqual(rebuild.rebuilt(data, tables), [])

    def test_major_and_minor_sides_are_separate(self):
        # 38 CFR 4.73, DC 5301: severe 40 dominant / 30 non-dominant (the 2020 data showed 30 with "Severe 40" in the text)
        self.assertEqual(rows("5301"), [(40, 30), (30, 20), (10, 10), (0, 0)])
        self.assertEqual([k["text"] for k in BY_CODE["5301"]["criteria"]], ["Severe", "Moderately Severe", "Moderate", "Slight"])
        # 38 CFR 4.124a, DC 8516 ulnar nerve
        self.assertEqual(rows("8516"), [(60, 50), (40, 30), (30, 20), (10, 10)])
        # 38 CFR 4.71a, DC 5202: every row keeps both sides
        self.assertEqual(rows("5202"), [(80, 70), (60, 50), (50, 40), (30, 20), (20, 20), (30, 20), (20, 20)])

    def test_lost_labels_and_bled_rows_are_repaired(self):
        self.assertEqual(BY_CODE["5136"]["criteria"], [{"percent": 60, "text": "Thumb, long and little", "percent_minor": 50}])
        self.assertEqual(BY_CODE["5230"]["criteria"], [{"percent": 0, "text": "Any limitation of motion", "percent_minor": 0}])
        self.assertIn("special monthly compensation", BY_CODE["5120"]["criteria"][0]["text"])
        for code in ("8710", "6091"):   # the official entry lists no rated rows; the 2020 rows came from neighbours
            self.assertEqual(BY_CODE[code]["criteria"], [], code)
            self.assertFalse(BY_CODE[code]["has_criteria"], code)

    def test_header_strip_leaves_regulation_wording(self):
        self.assertIn("General Rating Formula", BY_CODE["5243"]["criteria"][0]["text"])
        self.assertEqual(rows("5243"), [(60, None), (40, None), (20, None), (10, None)])

    def test_superseded_codes_are_not_replaced_with_current_text(self):
        c = BY_CODE["7308"]
        self.assertEqual(c["status"], "SUPERSEDED")
        self.assertTrue(c["criteria"][1]["text"].startswith("Moderate; less frequent episodes"))

    def test_rebuilt_codes_say_so(self):
        notes = {c.get("status_note") for c in BY_CODE.values()}
        self.assertTrue({rebuild.NOTE, rebuild.NOTE_COPIED, rebuild.NOTE_HEADER} <= notes)
        for c in BY_CODE.values():
            if any("percent_minor" in k for k in c["criteria"]):
                self.assertEqual(c["status_note"], rebuild.NOTE, c["code"])
                self.assertEqual(c["status"] if "status" in c else "UNVERIFIED", "UNVERIFIED")


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

    def test_bad_minor_percent(self):
        self.assertIn("percent_minor must be", self.mutate(lambda t: t["rating_criterion"][0].update(percent_minor=15)))

    def test_minor_side_above_major_side(self):
        self.assertIn("cannot rate above", self.mutate(lambda t: t["rating_criterion"][0].update(percent=10, percent_minor=20)))

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


    def test_db_refuses_bad_minor_percent(self):
        with connect(ADMIN_DSN) as conn:
            with self.assertRaises(DatabaseError):
                conn.query("INSERT INTO ref.rating_criterion (criterion_id, code, position, percent, percent_minor, criteria_text) "
                             "VALUES ('6847:99', '6847', 99, 10, 15, 'x')")

    def test_db_holds_both_sides(self):
        with connect(APP_DSN) as conn:
            r = conn.one("SELECT percent, percent_minor FROM ref.rating_criterion WHERE criterion_id = '5301:00'")
            self.assertEqual((r["percent"], r["percent_minor"]), (40, 30))


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

    def test_code_detail_carries_the_minor_side(self):
        j = self.client.get("/api/v1/reference/rating-schedule/5301").json()
        self.assertEqual([(c["percent"], c["percent_minor"]) for c in j["criteria"]], [(40, 30), (30, 20), (10, 10), (0, 0)])
        self.assertIn("4.69", j["code"]["status_note"])
        j = self.client.get("/api/v1/reference/rating-schedule/6847").json()
        self.assertTrue(all(c["percent_minor"] is None for c in j["criteria"]))

    def test_unknown_code_is_404(self):
        r = self.client.get("/api/v1/reference/rating-schedule/9999")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["error"]["code"], "UNKNOWN_RATING_CODE")


if __name__ == "__main__":
    unittest.main()
