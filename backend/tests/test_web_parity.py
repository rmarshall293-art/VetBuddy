"""Browser kernel (web/kernel.js) vs Python kernel: identical outputs on shared
golden fixtures (Field Manual step 24; governance release gate "browser and
server engines pass the same golden files"). Also fails if the generated
kernel data or standalone build is stale."""
import datetime as dt
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from app.domains.kernel import ratings
from app.domains.missions import router_policy as rp

ROOT = Path(__file__).resolve().parents[2]
TODAY = "2026-10-20"

ROUTER_FIXTURES = [
    dict(persona="guard_reserve", branch="Army", component="national_guard", legal_authority="unknown",
         separation_date="2027-06-30", current_jurisdiction="AL", destination_jurisdiction="TX",
         goals=["education", "career", "benefits"], urgency="30_days"),
    dict(persona="service_member", branch="Navy", component="active_duty", legal_authority=None,
         separation_date=None, current_jurisdiction="FL", destination_jurisdiction=None, goals=[], urgency="7_days"),
    dict(persona="veteran", branch="Marine Corps", component="medically_separated", legal_authority=None,
         separation_date="2026-09-01", current_jurisdiction="PR", destination_jurisdiction="PR",
         goals=["claims", "financial", "claims"], urgency="immediate"),
    dict(persona="spouse_family", branch="Coast Guard", component="reserve", legal_authority="title_10",
         separation_date="2030-01-01", current_jurisdiction="GU", destination_jurisdiction="AL",
         goals=["family", "housing", "community"], urgency="long_term"),
    dict(persona="veteran", branch="Air Force", component="retired", legal_authority=None,
         separation_date="2014-05-31", current_jurisdiction="TX", destination_jurisdiction=None,
         goals=["education"], urgency="info_only"),
] + [dict(persona="service_member", branch="Space Force", component="active_duty", legal_authority=None,
          separation_date=(dt.date(2026, 10, 20) + dt.timedelta(days=off)).isoformat(),
          current_jurisdiction="AL", destination_jurisdiction=None, goals=["career"], urgency="30_days")
     for off in (731, 730, 365, 181, 180, 91, 90, 31, 30, 0, -1, -30, -31, -91, -366, -1096, -1826)]

RATING_FIXTURES = [[50, 30], [40, 20], [60, 40, 20], [70, 50], [70, 50, 30], [100, 10], [10], [0], [30, 30, 30, 30],
                   [90, 90, 90], [20, 10, 10, 10, 10, 10]]
# (other ratings, bilateral ratings) for 38 CFR 4.26
BILATERAL_FIXTURES = [([], [30, 10]), ([], [40, 20]), ([50], [30, 20]), ([60, 10], [20, 20]), ([70], [50, 50, 10, 10]),
                      ([10, 10], [10, 10]), ([90, 30], [60, 40]), ([0], [0, 10]), ([], [40, 30, 20, 10]), ([100], [50, 50])]

NODE_SCRIPT = """
import { route, combineRatings } from %s;
const fx = JSON.parse(process.argv[1]);
const out = { routes: [], ratings: [], bilateral: [] };
for (const f of fx.routes) out.routes.push(await route(f, fx.today));
for (const r of fx.ratings) { const c = combineRatings(r); out.ratings.push([c.steps, c.combined_value, c.combined_rating]); }
for (const [o, b] of fx.bilateral) { const c = combineRatings(o, b);
  out.bilateral.push([c.steps, c.combined_value, c.combined_rating, c.bilateral.steps, c.bilateral.value_with_factor]); }
process.stdout.write(JSON.stringify(out));
"""


def py_route(f):
    inp = rp.RouterInput(**{**f, "goals": tuple(f["goals"]),
                            "separation_date": dt.date.fromisoformat(f["separation_date"]) if f["separation_date"] else None})
    return json.loads(json.dumps(rp.route(inp, dt.date.fromisoformat(TODAY)).to_dict()))


@unittest.skipUnless(shutil.which("node"), "node not installed")
class Parity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = NODE_SCRIPT % json.dumps((ROOT / "web/kernel.js").as_uri())
        res = subprocess.run(["node", "--input-type=module", "-e", script,
                              json.dumps({"routes": ROUTER_FIXTURES, "ratings": RATING_FIXTURES, "bilateral": BILATERAL_FIXTURES,
                                          "today": TODAY})],
                             capture_output=True, text=True, timeout=60)
        if res.returncode:
            raise AssertionError(res.stderr)
        cls.js = json.loads(res.stdout)

    def test_router_identical(self):
        for f, js in zip(ROUTER_FIXTURES, self.js["routes"]):
            with self.subTest(fixture=f):
                self.assertEqual(js, py_route(f))

    def test_ratings_identical(self):
        for r, js in zip(RATING_FIXTURES, self.js["ratings"]):
            with self.subTest(ratings=r):
                p = ratings.combine(r)
                self.assertEqual(js, [list(p.steps), p.combined_value, p.combined_rating])

    def test_bilateral_identical(self):
        for (o, b), js in zip(BILATERAL_FIXTURES, self.js["bilateral"]):
            with self.subTest(other=o, bilateral=b):
                p = ratings.combine(o, b)
                self.assertEqual(js, [list(p.steps), p.combined_value, p.combined_rating,
                                      list(p.bilateral.steps), p.bilateral.value_with_factor])


class GeneratedArtifactsCurrent(unittest.TestCase):
    def test_build_check(self):
        res = subprocess.run(["python3", str(ROOT / "scripts/build_web.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
