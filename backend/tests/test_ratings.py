"""38 CFR 4.25 combined ratings: the regulation's own examples, plus the A-01 ban."""

import ast
from pathlib import Path

import pytest

from app.kernel import ratings
from app.kernel.ratings import combine_ratings


@pytest.mark.parametrize("given,value,rating", [
    ([50, 30], 65, 70),          # 38 CFR 4.25(a) example
    ([40, 20], 52, 50),          # 38 CFR 4.25(a) example
    ([60, 40, 20], 81, 80),      # 38 CFR 4.25(a) example: 76 then 81
    ([30, 20, 10], 50, 50),
    ([10], 10, 10),
    ([0], 0, 0),
    ([100, 50], 100, 100),
    ([90, 90, 90, 90], 100, 100),  # 99.99 -> 100 via integer steps, capped
])
def test_regulation_examples(given, value, rating):
    r = combine_ratings(given)
    assert (r["combined_value"], r["combined_rating"]) == (value, rating)


def test_steps_and_order():
    r = combine_ratings([20, 60, 40])
    assert r["ratings"] == [60, 40, 20] and r["steps"] == [60, 76, 81]
    assert r["citation"] == "38 CFR 4.25" and r["bilateral_factor_applied"] is False


def test_half_rounds_up_once():
    # 50 + 30 -> 65 exactly; banker's rounding would give 60.
    assert combine_ratings([50, 30])["combined_rating"] == 70


@pytest.mark.parametrize("bad", [[], [15], [110], [-10], [True], ["50"], [50.0]])
def test_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        combine_ratings(bad)


def test_kernel_uses_integer_arithmetic_only():
    """Defect A-01: no float literals, true division, or round() in the kernel."""
    tree = ast.parse(Path(ratings.__file__).read_text())
    for node in ast.walk(tree):
        assert not (isinstance(node, ast.Constant) and isinstance(node.value, float)), "float literal"
        assert not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)), "true division"
        assert not (isinstance(node, ast.Call) and getattr(node.func, "id", None) in ("round", "float")), "round/float"
