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


# ── 38 CFR 4.26 bilateral factor (A-03) ──

@pytest.mark.parametrize("other,both,b_value,rating", [
    ([], [30, 10], 41, 40),        # 37, + 3.7 = 40.7 -> 41
    ([], [40, 20], 57, 60),        # 52, + 5.2 = 57.2 -> 57
    ([50], [30, 20], 48, 70),      # 44, + 4.4 = 48.4 -> 48; then 50 & 48 -> 74
    ([], [30, 20, 10, 10], 61, 60),  # 30,44,50,55; 55 + 5.5 = 60.5 -> 61 (half-up); 61 -> 60
])
def test_bilateral_factor(other, both, b_value, rating):
    r = combine_ratings(other, both)
    assert r["bilateral_factor_applied"] is True and r["bilateral"]["citation"] == "38 CFR 4.26"
    assert r["bilateral"]["value_with_factor"] == b_value
    assert r["combined_rating"] == rating


def test_bilateral_value_is_ordered_with_the_others():
    r = combine_ratings([40], [30, 20])  # bilateral 48 outranks 40
    assert r["ratings"] == [48, 40]


def test_bilateral_needs_both_sides():
    with pytest.raises(ValueError, match="both sides"):
        combine_ratings([50], [30])


def test_no_bilateral_is_unchanged():
    assert combine_ratings([60, 40, 20]) == combine_ratings([60, 40, 20], [])


def test_uploaded_app_float_defect_is_not_reproduced():
    """The uploaded rating app combined floats without per-step rounding and got 50 here; 4.25 gives 60."""
    assert combine_ratings([30, 20, 10, 10])["combined_rating"] == 60
