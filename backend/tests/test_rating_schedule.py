"""38 CFR Part 4 rating schedule as reference data (migrations 0017-0019).

The data is generated from the saved eCFR text by scripts/build_rating_schedule.py; these
tests pin it to the regulation. The schedule explains how VA describes criteria. It is
never matched against a veteran's symptoms (governance section 5), so the tests also prove
there is no symptom column, no symptom search, and nothing VERIFIED without a reviewer.
"""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

from app.domains.reference import corpus
from app.infra.db import DatabaseError, connect

from tests.support import ADMIN_DSN, APP_DSN, ApiCase

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import build_rating_schedule as builder  # noqa: E402

C = corpus.build()
DATA = json.loads((corpus.DATA / "rating_schedule.json").read_text())
BY_CODE = {c["code"]: c for c in DATA["codes"]}
FORMULAS = {f["formula_id"]: f for f in DATA["formulas"]}
MENTAL = "cfr4_4_130.general_rating_formula_for_mental_disorders"
HEART = "cfr4_4_104.general_rating_formula_for_diseases_of_the_heart"
EYE = "cfr4_4_79.general_rating_formula_for_diseases_of_the_eye"
# Signs of the 2020 PDF transcription's damage: page headers, running heads, column headings,
# a rating number left at the end of the text, a row that is only a number.
DAMAGE = re.compile(r"—\s*Continued|Major Minor|\[\[PAGE \d+\]\]|7–1–20 Edition|(?<!Stage)\s(?:0|[1-9]0|100)\s*$|^\s*\d{1,3}\s*$")


def rows(code):
    return [(k["percent"], k.get("percent_minor")) for k in BY_CODE[code]["criteria"]]


def formula_pcts(fid):
    return [k["percent"] for k in FORMULAS[fid]["criteria"]]


class MatchesTheRegulation(unittest.TestCase):
    def test_dataset_is_exactly_what_the_snapshot_gives(self):
        from xml.etree import ElementTree as ET
        former = json.loads(builder.FORMER_NAMES.read_text())["names"]
        self.assertEqual(builder.build(ET.parse(builder.SNAPSHOT).getroot(), former), DATA)

    def test_counts(self):
        self.assertEqual(len(DATA["codes"]), 753)
        by = {}
        for c in DATA["codes"]:
            by[c["status"]] = by.get(c["status"], 0) + 1
        self.assertEqual(by, {"SOURCE_CHECKED": 721, "SUPERSEDED": 32})
        self.assertEqual(len(DATA["formulas"]), 23)
        self.assertEqual(sum(c["has_criteria"] for c in DATA["codes"]), 419)

    def test_no_row_shows_pdf_parse_damage(self):
        bad = [(c["code"], k["text"][-60:]) for c in DATA["codes"] for k in c["criteria"] if DAMAGE.search(k["text"])]
        bad += [(f["formula_id"], k["text"][-60:]) for f in DATA["formulas"] for k in f["criteria"] if DAMAGE.search(k["text"])]
        self.assertEqual(bad, [])

    def test_major_and_minor_sides_are_separate(self):
        # 38 CFR 4.73, DC 5301: severe 40 dominant / 30 non-dominant
        self.assertEqual(rows("5301"), [(40, 30), (30, 20), (10, 10), (0, 0)])
        self.assertEqual([k["text"] for k in BY_CODE["5301"]["criteria"]], ["Severe", "Moderately Severe", "Moderate", "Slight"])
        self.assertEqual(rows("8516"), [(60, 50), (40, 30), (30, 20), (10, 10)])           # ulnar nerve, 4.124a
        self.assertEqual(rows("5202"), [(80, 70), (60, 50), (50, 40), (30, 20), (20, 20), (30, 20), (20, 20)])
        self.assertEqual(rows("5136"), [(60, 50)])
        self.assertEqual(rows("5230"), [(0, 0)])
        self.assertIn("special monthly compensation", BY_CODE["5120"]["criteria"][0]["text"])

    def test_single_rating_codes(self):
        self.assertEqual(rows("6847"), [(100, None), (50, None), (30, None), (0, None)])     # sleep apnea
        self.assertEqual(rows("7523"), [(20, None), (0, None)])                              # rating printed in the label
        self.assertEqual([k["text"].split(" (")[0] for k in BY_CODE["7523"]["criteria"]], ["Both", "One"])

    def test_formulas(self):
        self.assertEqual(formula_pcts(MENTAL), [100, 70, 50, 30, 10, 0])
        self.assertEqual(formula_pcts(HEART), [100, 60, 30, 10])
        self.assertEqual(formula_pcts(EYE), [60, 40, 20, 10])
        skin = next(f for f in DATA["formulas"] if f["formula_id"].startswith("cfr4_4_118.general_rating_formula_for_the_skin"))
        self.assertEqual([k["percent"] for k in skin["criteria"]], [60, 30, 10, 0])
        # eCFR prints the items of each level flat; every level keeps its own items
        self.assertIn("more than 40 percent", skin["criteria"][0]["text"])
        self.assertIn("Constant or near-constant systemic therapy", skin["criteria"][0]["text"])
        self.assertIn("20 to 40 percent", skin["criteria"][1]["text"])
        self.assertIn("at least 5 percent, but less than 20 percent", skin["criteria"][2]["text"])
        self.assertIn("less than 5 percent", skin["criteria"][3]["text"])

    def test_codes_link_only_where_the_regulation_says(self):
        expect = {
            "9411": {MENTAL},                                                   # 4.130 note: DCs 9201 to 9440
            "9520": {"cfr4_4_130.rating_formula_for_eating_disorders"},
            "7005": {HEART},                                                    # heart caption: unless otherwise directed
            "6000": {EYE},                                                      # printed directly after the eye formula
            "6091": {EYE},                                                      # "Evaluate under the General Rating Formula for Diseases of the Eye"
            "7504": {"cfr4_4_115a.renal_dysfunction", "cfr4_4_115a.urinary_tract_infection"},
        }
        for code, fids in expect.items():
            self.assertEqual(set(BY_CODE[code]["formula_ids"]), fids, code)
        self.assertEqual(len(BY_CODE["5243"]["formula_ids"]), 2)                # spine formula or IVDS formula
        self.assertTrue(BY_CODE["6510"]["formula_ids"][0].startswith("cfr4_4_97.general_rating_formula_for_sinusitis"))
        self.assertTrue(BY_CODE["6721"]["formula_ids"][0].startswith("cfr4_4_97.general_rating_formula_for_inactive_pulmonary"))
        self.assertEqual(BY_CODE["7204"]["cited_codes"], ["7203"])              # "Rate as esophagus, stricture of (DC 7203)"
        # the regulation lists no rows under 8710 (neuralgia); the 2020 data had copied 8510's
        self.assertEqual((BY_CODE["8710"]["criteria"], BY_CODE["8710"]["formula_ids"]), ([], []))

    def test_grouped_codes_share_their_rows(self):
        # "7000 Valvular heart disease, 7001 Endocarditis, or 7002 Pericarditis:" share 7002's rows
        for code in ("7000", "7001"):
            self.assertEqual(rows(code), rows("7002"), code)
            self.assertIn("7002", BY_CODE[code]["status_note"])

    def test_names_are_the_current_index(self):
        self.assertEqual(BY_CODE["6847"]["name"], "Sleep Apnea Syndromes")
        self.assertEqual(BY_CODE["9411"]["name"], "Posttraumatic stress disorder")
        self.assertTrue(BY_CODE["5002"]["name"].startswith("Multi-joint arthritis"))   # renamed 2021
        for invented in ("9420", "9999", "8110", "6814", "6848", "6399"):              # from the rejected va_claims_data.json
            self.assertNotIn(invented, BY_CODE)

    def test_removed_codes_say_when(self):
        self.assertEqual(BY_CODE["7305"]["status"], "SUPERSEDED")
        self.assertIn("Removed May 19, 2024", BY_CODE["7305"]["status_note"])
        self.assertIn("removed November 14, 2021", BY_CODE["7510"]["status_note"])
        self.assertEqual(BY_CODE["6067"]["status"], "SUPERSEDED")                      # only the index still lists it
        for c in DATA["codes"]:
            if c["status"] == "SUPERSEDED":
                self.assertEqual((c["criteria"], c["formula_ids"]), ([], []), c["code"])
        digestive = [c for c in DATA["codes"] if c["body_system"] == "THE DIGESTIVE SYSTEM" and c["status"] != "SUPERSEDED"]
        self.assertEqual(len(digestive), 51)                                            # current 2024 text, no longer superseded

    def test_nothing_is_verified_by_a_script(self):
        self.assertTrue(all(c["status"] in ("SOURCE_CHECKED", "SUPERSEDED") for c in DATA["codes"]))
        self.assertTrue(all("status" not in f or f["status"] != "VERIFIED" for f in DATA["formulas"]))

    def test_no_symptom_columns_anywhere(self):
        for table in ("rating_code", "rating_criterion", "rating_formula", "rating_formula_criterion"):
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
        self.assertIn("steps of 10", self.mutate(lambda t: t["rating_formula_criterion"][0].update(percent=15)))

    def test_bad_minor_percent(self):
        self.assertIn("percent_minor must be", self.mutate(lambda t: t["rating_criterion"][0].update(percent_minor=15)))

    def test_minor_side_above_major_side(self):
        self.assertIn("cannot rate above", self.mutate(lambda t: t["rating_criterion"][0].update(percent=10, percent_minor=20)))

    def test_orphan_rows_and_links(self):
        self.assertIn("unknown code", self.mutate(lambda t: t["rating_criterion"][0].update(code="0000")))
        self.assertIn("unknown formula", self.mutate(lambda t: t["rating_formula_criterion"][0].update(formula_id="cfr4_x.y")))
        self.assertIn("unknown code or formula", self.mutate(lambda t: t["rating_code_formula"][0].update(formula_id="cfr4_x.y")))
        self.assertIn("cites unknown codes", self.mutate(lambda t: t["rating_code"][0].update(cited_codes=["0001"])))


class Database(unittest.TestCase):
    def test_loaded_and_read_only_for_app(self):
        with connect(APP_DSN) as conn:
            self.assertEqual(conn.one("SELECT count(*) AS n FROM ref.rating_code")["n"], 753)
            self.assertEqual(conn.one("SELECT count(*) AS n FROM ref.rating_formula")["n"], 23)
            with self.assertRaises(DatabaseError):
                conn.query("UPDATE ref.rating_code SET status = 'VERIFIED' WHERE code = '6847'")

    def test_db_refuses_verified_without_reviewer_even_for_owner(self):
        with connect(ADMIN_DSN) as conn:
            for sql in ("UPDATE ref.rating_code SET status = 'VERIFIED' WHERE code = '6847'",
                        f"UPDATE ref.rating_formula SET status = 'VERIFIED' WHERE formula_id = '{MENTAL}'"):
                with self.assertRaises(DatabaseError):
                    conn.query(sql)

    def test_db_refuses_bad_percent(self):
        with connect(ADMIN_DSN) as conn:
            for sql in ("INSERT INTO ref.rating_criterion (criterion_id, code, position, percent, criteria_text) "
                        "VALUES ('6847:99', '6847', 99, 15, 'x')",
                        "INSERT INTO ref.rating_criterion (criterion_id, code, position, percent, percent_minor, criteria_text) "
                        "VALUES ('6847:98', '6847', 98, 10, 15, 'x')",
                        "INSERT INTO ref.rating_formula_criterion (criterion_id, formula_id, position, percent, criteria_text) "
                        f"VALUES ('x:99', '{MENTAL}', 99, 15, 'x')"):
                with self.assertRaises(DatabaseError):
                    conn.query(sql)

    def test_db_holds_both_sides_and_the_links(self):
        with connect(APP_DSN) as conn:
            r = conn.one("SELECT percent, percent_minor FROM ref.rating_criterion WHERE criterion_id = '5301:00'")
            self.assertEqual((r["percent"], r["percent_minor"]), (40, 30))
            n = conn.one("SELECT count(*) AS n FROM ref.rating_code_formula WHERE formula_id = $1", [MENTAL])["n"]
            self.assertEqual(n, len([c for c in DATA["codes"] if MENTAL in c["formula_ids"]]))


class Api(ApiCase):
    def test_index_has_no_symptom_search(self):
        j = self.client.get("/api/v1/reference/rating-schedule?body_system=THE%20EAR").json()
        self.assertEqual({r["body_system"] for r in j["codes"]}, {"THE EAR"})
        self.assertIn("not an assessment of your condition", j["label"])
        self.assertIn("accredited", j["vso_referral"])
        self.assertNotIn("criteria", j["codes"][0])
        self.assertEqual(len(j["formulas"]), 23)
        self.assertEqual(len(self.client.get("/api/v1/reference/rating-schedule?q=back%20pain").json()["codes"]), 753)

    def test_code_detail(self):
        j = self.client.get("/api/v1/reference/rating-schedule/6847").json()
        self.assertEqual(j["code"]["name"], "Sleep Apnea Syndromes")
        self.assertEqual(j["code"]["status"], "SOURCE_CHECKED")
        self.assertEqual([c["percent"] for c in j["criteria"]], [100, 50, 30, 0])
        self.assertTrue(all(c["percent_minor"] is None for c in j["criteria"]))

    def test_code_detail_carries_the_minor_side(self):
        j = self.client.get("/api/v1/reference/rating-schedule/5301").json()
        self.assertEqual([(c["percent"], c["percent_minor"]) for c in j["criteria"]], [(40, 30), (30, 20), (10, 10), (0, 0)])

    def test_code_detail_carries_its_formula(self):
        j = self.client.get("/api/v1/reference/rating-schedule/9411").json()
        self.assertEqual(j["criteria"], [])
        self.assertEqual([f["formula_id"] for f in j["formulas"]], [MENTAL])
        self.assertEqual([c["percent"] for c in j["formulas"][0]["criteria"]], [100, 70, 50, 30, 10, 0])

    def test_unknown_code_is_404(self):
        r = self.client.get("/api/v1/reference/rating-schedule/9999")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["error"]["code"], "UNKNOWN_RATING_CODE")


if __name__ == "__main__":
    unittest.main()
