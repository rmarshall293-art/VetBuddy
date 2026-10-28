"""38 CFR 4.25 combined-rating kernel. Expected values come from the
regulation's own worked examples, not from the implementation."""
import ast
import itertools
import unittest
from pathlib import Path

from app.domains.kernel import ratings


class RegulationExamples(unittest.TestCase):
    def test_examples_from_4_25(self):
        cases = [([50, 30], [50, 65], 65, 70),
                 ([40, 20], [40, 52], 52, 50),
                 ([60, 40, 20], [60, 76, 81], 81, 80)]
        for given, steps, value, final in cases:
            with self.subTest(given=given):
                r = ratings.combine(given)
                self.assertEqual(list(r.steps), steps)
                self.assertEqual(r.combined_value, value)
                self.assertEqual(r.combined_rating, final)

    def test_banker_rounding_regression_A01(self):
        # 70 + 50 -> 85, which must convert UP to 90 (banker's rounding gave 80).
        self.assertEqual(ratings.combine([70, 50]).combined_rating, 90)
        self.assertEqual(ratings.combine([50, 30]).combined_rating, 70)   # 65 -> 70

    def test_intermediate_half_up(self):
        # 85 then 30: 15 * 0.30 = 4.5 -> Table I value 90 (half-up), not 89.
        self.assertEqual(ratings.combine([70, 50, 30]).steps, (70, 85, 90))

    def test_order_independent(self):
        base = ratings.combine([30, 70, 10, 50])
        for perm in itertools.permutations([30, 70, 10, 50]):
            self.assertEqual(ratings.combine(list(perm)), base)

    def test_bounds(self):
        self.assertEqual(ratings.combine([100, 50]).combined_rating, 100)
        self.assertEqual(ratings.combine([0]).combined_rating, 0)
        self.assertEqual(ratings.combine([10]).combined_rating, 10)
        for bad in ([], [15], [110], [-10], [True], [50.0]):
            with self.subTest(bad=bad), self.assertRaises(ratings.RatingInputError):
                ratings.combine(bad)

    def test_bilateral_factor_is_declared_unapplied(self):
        self.assertFalse(ratings.combine([20, 20]).bilateral_factor_applied)


class BilateralFactor(unittest.TestCase):
    """38 CFR 4.26 (A-03). Worked by hand: combine the paired ratings, add 10% of
    that value (not combined), round half-up, then treat it as one rating."""
    def test_worked_examples(self):
        cases = [([], [30, 10], 41, 40),          # 37 + 3.7 = 40.7 -> 41
                 ([], [40, 20], 57, 60),          # 52 + 5.2 = 57.2 -> 57
                 ([50], [30, 20], 48, 70),        # 44 + 4.4 = 48.4 -> 48; 50 & 48 -> 74
                 ([], [30, 20, 10, 10], 61, 60)]  # 55 + 5.5 = 60.5 -> 61 (half-up)
        for other, both, value, final in cases:
            with self.subTest(other=other, both=both):
                r = ratings.combine(other, both)
                self.assertTrue(r.bilateral_factor_applied)
                self.assertEqual(r.bilateral.value_with_factor, value)
                self.assertEqual(r.combined_rating, final)
                self.assertEqual(r.bilateral.citation, "38 CFR 4.26")

    def test_bilateral_value_is_ordered_with_the_others(self):
        self.assertEqual(ratings.combine([40], [30, 20]).ratings, (48, 40))

    def test_needs_both_sides(self):
        with self.assertRaises(ratings.RatingInputError):
            ratings.combine([50], [30])

    def test_float_defect_of_uploaded_app_not_reproduced(self):
        # The uploaded va-rating-app combined unrounded floats and got 50 here.
        self.assertEqual(ratings.combine([30, 20, 10, 10]).combined_rating, 60)


class Purity(unittest.TestCase):
    """Plane-2 rule: no float literal, no float(), no round(), no I/O imports."""
    def test_ast(self):
        tree = ast.parse(Path(ratings.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                self.fail(f"float literal at line {node.lineno}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("float", "round", "open"):
                self.fail(f"{node.func.id}() at line {node.lineno}")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) else [])
                for n in names:
                    self.assertNotIn(n, ("os", "socket", "requests", "datetime", "time", "random"), f"I/O import {n}")


if __name__ == "__main__":
    unittest.main()
