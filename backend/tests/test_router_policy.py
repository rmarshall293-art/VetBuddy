"""Pure, DB-free tests for the deterministic Mission Router (phase P3 gate:
different personas route differently and reproducibly, no AI involved)."""
import datetime as dt
import re
import unittest

from app.domains.missions import router_policy as rp
from app.domains.missions.task_library import TEMPLATES

TODAY = dt.date(2026, 10, 20)
JUR = {"FEDERAL", "AL", "TX", "PR", "GU"}


def make(**kw) -> rp.RouterInput:
    base = dict(persona="service_member", branch="Army", component="active_duty", legal_authority=None,
                separation_date=dt.date(2027, 3, 1), current_jurisdiction="AL", destination_jurisdiction=None,
                goals=("career",), urgency="30_days")
    base.update(kw)
    return rp.RouterInput(**base)


class StageTests(unittest.TestCase):
    def test_boundaries(self):
        cases = [(731, "in_service"), (730, "t_24_12m"), (366, "t_24_12m"), (365, "t_12_6m"), (181, "t_12_6m"),
                 (180, "t_180_90d"), (91, "t_180_90d"), (90, "t_90_30d"), (31, "t_90_30d"), (30, "t_30d_sep"),
                 (0, "t_30d_sep"), (-1, "day_0_30"), (-30, "day_0_30"), (-31, "day_31_90"), (-90, "day_31_90"),
                 (-91, "month_3_12"), (-365, "month_3_12"), (-366, "year_1_2"), (-730, "year_1_2"),
                 (-731, "year_2_3"), (-1095, "year_2_3"), (-1096, "year_3_5"), (-1825, "year_3_5"),
                 (-1826, "ongoing")]
        for offset, expected in cases:
            with self.subTest(offset=offset):
                stage, days = rp.compute_stage(TODAY + dt.timedelta(days=offset), TODAY)
                self.assertEqual(stage, expected)
                self.assertEqual(days, offset)

    def test_unknown_date_is_not_guessed(self):
        out = rp.route(make(separation_date=None), TODAY)
        self.assertEqual(out.stage, "unknown")
        ids = [t.template_id for t in out.tasks]
        self.assertIn("FACT-DATE", ids)
        self.assertNotIn("TAP-01", ids, "stage-bound tasks must not appear when the stage is unknown")
        self.assertIn("STAGE_UNKNOWN", [n["code"] for n in out.notices])


class DeterminismTests(unittest.TestCase):
    def test_same_input_same_output(self):
        a = rp.route(make(goals=("education", "career")), TODAY).to_dict()
        b = rp.route(make(goals=("career", "education", "career")), TODAY).to_dict()
        self.assertEqual(a, b, "goal order/duplicates must not change the output")

    def test_hash_changes_with_input(self):
        self.assertNotEqual(make().digest(), make(current_jurisdiction="TX").digest())

    def test_two_personas_route_differently(self):
        ad = rp.route(make(), TODAY)
        gr = rp.route(make(persona="guard_reserve", component="national_guard", legal_authority="title_32",
                           current_jurisdiction="PR"), TODAY)
        self.assertEqual(ad.track, "ets_eas")
        self.assertEqual(gr.track, "guard_reserve")
        self.assertIn("guard_reserve", gr.lanes)
        self.assertNotIn("guard_reserve", ad.lanes)
        self.assertIn("GR-RECORD", [t.template_id for t in gr.tasks])
        self.assertNotIn("GR-AUTH", [t.template_id for t in gr.tasks], "authority was declared, do not ask")

    def test_guard_unknown_authority_asks_for_orders(self):
        out = rp.route(make(component="reserve", legal_authority="unknown"), TODAY)
        self.assertIn("GR-AUTH", [t.template_id for t in out.tasks])
        self.assertIn("AUTHORITY_UNKNOWN", [n["code"] for n in out.notices])

    def test_relocation_adds_state_lane(self):
        out = rp.route(make(destination_jurisdiction="TX"), TODAY)
        self.assertIn("state_local", out.lanes)
        self.assertEqual(out.track, "pcs")

    def test_medical_separation_track(self):
        out = rp.route(make(component="medically_separated", persona="veteran",
                            separation_date=TODAY - dt.timedelta(days=10)), TODAY)
        self.assertEqual(out.track, "medical_separation")
        self.assertIn("MED-01", [t.template_id for t in out.tasks])

    def test_benefit_screening_is_withheld(self):
        out = rp.route(make(goals=("benefits",)), TODAY)
        self.assertEqual(out.notices[0]["code"], "BENEFIT_SCREENING_NOT_AVAILABLE")


class ValidationTests(unittest.TestCase):
    def test_guard_requires_authority(self):
        with self.assertRaises(rp.RouterInputError) as e:
            rp.validate(make(component="national_guard", legal_authority=None), JUR)
        self.assertEqual(e.exception.field, "legal_authority")

    def test_unknown_jurisdiction(self):
        with self.assertRaises(rp.RouterInputError):
            rp.validate(make(current_jurisdiction="ZZ"), JUR)

    def test_bad_goal(self):
        with self.assertRaises(rp.RouterInputError):
            rp.validate(make(goals=("lottery",)), JUR)


class ContentSafetyTests(unittest.TestCase):
    """Zero invented official facts: task copy may not assert eligibility,
    guarantees, amounts, rates or legal deadlines."""
    FORBIDDEN = [r"\byou (are|will be) eligible\b", r"\byou qualify\b", r"\bguarantee", r"\$\s?\d",
                 r"\b\d+\s?%", r"\bdeadline is\b", r"\bmust file\b", r"\bis required by law\b", r"\bapproved\b"]

    def test_task_copy(self):
        for t in TEMPLATES.values():
            text = f"{t.title} {t.why}".lower()
            for pat in self.FORBIDDEN:
                with self.subTest(template=t.template_id, pattern=pat):
                    self.assertIsNone(re.search(pat, text))

    def test_readiness_is_not_a_score(self):
        r = rp.readiness([{"readiness_dimension": "documents", "status": "done"},
                          {"readiness_dimension": "documents", "status": "todo"}])
        self.assertEqual(len(r), 10)
        doc = next(x for x in r if x["dimension"] == "documents")
        self.assertEqual((doc["status"], doc["done"], doc["total"]), ("in_progress", 1, 2))
        self.assertTrue(all("score" not in x for x in r))


if __name__ == "__main__":
    unittest.main()
