"""k-anonymity aggregation (app/domains/insights/geo_aggregation.py).

Each GA defect from integration has a reproduction here, plus a randomized
attacker check: with every released figure and every line total in hand, no
withheld group, and no sum of withheld groups under k, can be worked out.
"""
import random
import unittest

from app.domains.insights import geo_aggregation as ga

K = ga.DEFAULT_K_THRESHOLD


def people(**counts):
    """people(county_fips={'01001': 12, '01003': 3}) -> list of records."""
    (dim, spec), = counts.items()
    return [{dim: key, "state_code": "AL"} for key, n in spec.items() for _ in range(n)]


class Rules(unittest.TestCase):
    def test_k_floor_and_dimension_lists(self):
        with self.assertRaises(ga.AggregationError):
            ga.aggregate([], "county_fips", k_threshold=5)
        for dim in ("pay_grade", "occupation_code", "va_rating", "diagnosis", "zip_code", "tenant_id"):
            with self.assertRaises(ga.AggregationError, msg=dim):
                ga.aggregate([], dim)
        with self.assertRaises(ga.AggregationError):
            ga.aggregate([], "favorite_color")
        self.assertFalse(ga.PERMITTED_AGGREGATE_DIMENSIONS & ga.FORBIDDEN_AGGREGATE_DIMENSIONS)

    def test_suppressed_cells_carry_no_count(self):
        out = ga.aggregate(people(county_fips={"A": 30, "B": 2, "C": 4}), "county_fips").to_dict()
        for cell in out["suppressed"].values():
            self.assertEqual(cell, {"suppressed": True, "reason": cell["reason"], "count": None})
        self.assertIn("NOT a zero", out["suppression_note"])

    def test_ga01_single_withheld_cell_is_not_recoverable_from_the_total(self):
        # Received behaviour: A=30 released, B=3 withheld, total 33 published -> B = 3.
        agg = ga.aggregate(people(county_fips={"A": 30, "B": 3}), "county_fips")
        self.assertEqual(agg.released, {})
        self.assertEqual(set(agg.suppressed), {"A", "B"})

    def test_ga05_small_sum_of_withheld_cells_is_not_released(self):
        # Received behaviour: two withheld cells (3 and 4) -> "7 across B and C" by subtraction.
        agg = ga.aggregate(people(county_fips={"A": 30, "D": 40, "B": 3, "C": 4}), "county_fips")
        self.assertEqual(agg.released, {"D": 40})
        self.assertEqual(set(agg.suppressed), {"A", "B", "C"})

    def test_ga02_columns_are_guarded_as_well_as_rows(self):
        recs = ([{"county_fips": "X", "top_career_cluster": "IT"}] * 20
                + [{"county_fips": "X", "top_career_cluster": "Health"}] * 15
                + [{"county_fips": "Y", "top_career_cluster": "IT"}] * 25
                + [{"county_fips": "Y", "top_career_cluster": "Health"}] * 2
                + [{"county_fips": "Z", "top_career_cluster": "Health"}] * 30
                + [{"county_fips": "Z", "top_career_cluster": "IT"}] * 14)
        tab = ga.cross_tabulate(recs, "county_fips", "top_career_cluster")
        cells = {(a, b): n for a, row in tab["rows"].items() for b, n in row["released"].items()}
        # (Y, Health)=2 is withheld; the row guard withholds (Y, IT); the column guard must also act on Health.
        self.assertNotIn(("Y", "IT"), cells)
        attack_cross_tab(self, recs, tab)

    def test_ga03_domain_hides_whether_a_group_is_empty(self):
        open_ = ga.aggregate(people(county_fips={"A": 40, "B": 2, "C": 30}), "county_fips")
        self.assertIn("at least one", open_.to_dict()["suppression_note"])
        closed = ga.aggregate(people(county_fips={"A": 40, "B": 2, "C": 30}), "county_fips",
                              domain=["A", "B", "C", "D", "E"])
        self.assertTrue({"B", "D", "E"} <= set(closed.suppressed))
        self.assertNotIn("at least one", closed.to_dict()["suppression_note"])
        with self.assertRaises(ga.AggregationError):
            ga.aggregate(people(county_fips={"Q": 12}), "county_fips", domain=["A"])

    def test_state_report_has_no_forbidden_fields_and_withholds_small_totals(self):
        recs = [dict(r, top_career_cluster="IT", education_gap_category="none", pay_grade="E-6")
                for r in people(county_fips={"01001": 5})]
        rep = ga.state_agency_report(recs, "AL")
        self.assertIsNone(rep["total_consented_users"])
        self.assertNotIn("E-6", repr(rep))
        self.assertIn("not all veterans", rep["methodology"]["not_a_population_estimate"])


def attack_line(case, counts: dict, released: dict, suppressed: set, label=""):
    """An attacker who knows the line total and every released cell."""
    for key, n in released.items():
        case.assertGreaterEqual(n, K, label)
    if suppressed and released:
        hidden = sum(counts.get(key, 0) for key in suppressed)
        case.assertGreaterEqual(hidden, K, f"{label}: withheld cells sum to {hidden}, recoverable by subtraction")


def attack_cross_tab(case, recs, tab):
    cells = {}
    for r in recs:
        cells[(r["county_fips"], r["top_career_cluster"])] = cells.get((r["county_fips"], r["top_career_cluster"]), 0) + 1
    rel = {(a, b): n for a, row in tab["rows"].items() for b, n in row["released"].items()}
    sup = {(a, b) for a, row in tab["rows"].items() for b in row["suppressed"]}
    case.assertEqual(set(rel) | sup, set(cells))
    for axis in (0, 1):
        for line in {c[axis] for c in cells}:
            attack_line(case, cells, {c: n for c, n in rel.items() if c[axis] == line},
                        {c for c in sup if c[axis] == line}, f"axis {axis} line {line}")


class RandomizedAttacker(unittest.TestCase):
    def test_no_line_leaks_under_random_populations(self):
        rng = random.Random(20261027)
        counties = [f"01{n:03d}" for n in range(1, 13, 2)]
        clusters = ["IT", "Health", "Logistics", "Trades", "Public safety"]
        for trial in range(300):
            recs = []
            for c in counties:
                for cl in clusters:
                    n = rng.choice([0, 0, 1, 2, 3, 5, 8, 10, 11, 12, 15, 25, 40])
                    recs += [{"county_fips": c, "top_career_cluster": cl, "state_code": "AL"}] * n
            with self.subTest(trial=trial):
                for dim in ("county_fips", "top_career_cluster"):
                    agg = ga.aggregate(recs, dim)
                    counts = {}
                    for r in recs:
                        counts[r[dim]] = counts.get(r[dim], 0) + 1
                    attack_line(self, counts, agg.released, set(agg.suppressed), dim)
                attack_cross_tab(self, recs, ga.cross_tabulate(recs, "county_fips", "top_career_cluster"))
