"""
Combined disability rating — 38 CFR 4.25 (Plane 2 kernel: pure, no I/O).

Source (verified 2026-10-20, eCFR via LII, https://www.law.cornell.edu/cfr/text/38/4.25):
  * Disabilities are arranged in order of severity and combined pairwise
    using Table I; with three or more, "the combined value, exactly as
    found in table I, will be combined with the degree of the third".
  * "The conversion to the nearest degree divisible by 10 will be done only
    once per rating decision", after all disabilities are combined, and
    "combined values ending in 5 will be adjusted upward".
  * Regulation examples: 50+30 -> 65 -> 70; 40+20 -> 52 -> 50;
    60+40+20 -> 76 -> 81 -> 80.

Table I entries are whole numbers. Each pairwise step here is
    combined + round_half_up(remaining_efficiency * rating / 100)
in exact integer arithmetic, which reproduces those examples. No float and
no built-in round() are used anywhere in this module (banker's rounding was
defect A-01; an AST test enforces this).

Bilateral factor (38 CFR 4.26, closes A-03): ratings the user marks as
affecting both arms or both legs (paired extremities) are combined first;
10% of that combined value is ADDED (not combined), rounded half-up to a
whole number, and the result is treated as one disability, placed in order
of severity among the others for all further combining.

NOT MODELED: Table I verification cell by cell, and anything VA decides
about which conditions are rated or whether they are bilateral.
This is an educational calculator, not a rating.
"""
from __future__ import annotations

from dataclasses import dataclass

CITATION = "38 CFR 4.25"
BILATERAL_CITATION = "38 CFR 4.26"
SOURCE_URL = "https://www.law.cornell.edu/cfr/text/38/4.25"
SOURCE_CHECKED = "2026-10-20"


class RatingInputError(ValueError):
    pass


@dataclass(frozen=True)
class CombinedRating:
    ratings: tuple[int, ...]       # as entered, sorted most to least severe
    steps: tuple[int, ...]         # combined value after each pairwise step (Table I values)
    combined_value: int            # final Table I value, before conversion
    combined_rating: int           # converted once to nearest 10, 5s up
    citation: str = CITATION
    bilateral_factor_applied: bool = False
    bilateral: "BilateralStep | None" = None


@dataclass(frozen=True)
class BilateralStep:
    ratings: tuple[int, ...]       # the paired-extremity ratings, most to least severe
    steps: tuple[int, ...]         # their own Table I combination
    combined_value: int            # combined bilateral value before the factor
    factor_tenths: int             # 10% of combined_value, in tenths of a percent
    value_with_factor: int         # combined_value + factor, rounded half-up; enters the main combination
    citation: str = BILATERAL_CITATION


def _half_up_div(numerator: int, denominator: int) -> int:
    return (2 * numerator + denominator) // (2 * denominator)


def _check(ratings) -> None:
    for r in ratings:
        if isinstance(r, bool) or not isinstance(r, int) or r < 0 or r > 100 or r % 10 != 0:
            raise RatingInputError(f"each rating must be a whole multiple of 10 from 0 to 100 (got {r!r})")


def _table_i(values) -> tuple[tuple[int, ...], tuple[int, ...]]:
    ordered = tuple(sorted(values, reverse=True))
    combined = ordered[0]
    steps = [combined]
    for r in ordered[1:]:
        remaining = 100 - combined
        combined = combined + _half_up_div(remaining * r, 100)
        steps.append(combined)
    return ordered, tuple(steps)


def combine(ratings: list[int] | tuple[int, ...], bilateral: list[int] | tuple[int, ...] = ()) -> CombinedRating:
    """`ratings` are the other disabilities; `bilateral` are those affecting paired extremities."""
    if not ratings and not bilateral:
        raise RatingInputError("at least one rating is required")
    _check(ratings)
    _check(bilateral)
    if len(bilateral) == 1:
        raise RatingInputError("the bilateral factor needs ratings on both sides (at least two)")
    values = list(ratings)
    step = None
    if bilateral:
        b_ordered, b_steps = _table_i(bilateral)
        b_value = b_steps[-1]
        step = BilateralStep(b_ordered, b_steps, b_value, b_value, _half_up_div(11 * b_value, 10))
        values.append(step.value_with_factor)
    ordered, steps = _table_i(values)
    combined = steps[-1]
    final = ((combined + 5) // 10) * 10
    return CombinedRating(ordered, steps, combined, min(final, 100), bilateral_factor_applied=step is not None,
                          bilateral=step)
