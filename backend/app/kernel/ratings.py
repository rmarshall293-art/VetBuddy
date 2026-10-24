"""Combined disability rating arithmetic, 38 CFR 4.25 and 4.26 (educational only).

Integer arithmetic throughout (defect A-01 was float + banker's rounding): each
Table I step rounds half-up to a whole number, and the combined value is
converted to the nearest 10 exactly once, with 5s rounding up.

Bilateral factor (38 CFR 4.26, closes A-03): ratings the user marks as
affecting both arms or both legs (paired extremities) are combined first; 10%
of that combined value is ADDED (not combined), rounded half-up to a whole
number, and the result is then treated as one disability, placed in order of
severity among the others for all further combining.

This is arithmetic on numbers the user enters, never a prediction of what VA
will rate (governance §5). frontend/src/kernel.js mirrors it; the parity test
proves they agree.
"""

from __future__ import annotations

CITATION = "38 CFR 4.25"
BILATERAL_CITATION = "38 CFR 4.26"


def _check(ratings: list[int]) -> None:
    for r in ratings:
        if isinstance(r, bool) or not isinstance(r, int) or r < 0 or r > 100 or r % 10:
            raise ValueError("each rating must be a whole multiple of 10 from 0 to 100")


def _combine(values: list[int]) -> tuple[list[int], list[int]]:
    """Combine whole-number values per Table I; returns (ordered values, running combined values)."""
    ordered = sorted(values, reverse=True)
    combined = ordered[0]
    steps = [combined]
    for v in ordered[1:]:
        combined += (2 * (100 - combined) * v + 100) // 200  # (100-c)*v/100 rounded half-up, in integers
        steps.append(combined)
    return ordered, steps


def combine_ratings(ratings: list[int], bilateral: list[int] | None = None) -> dict:
    """`ratings` are the other disabilities; `bilateral` are those affecting paired extremities."""
    bilateral = list(bilateral or [])
    if not ratings and not bilateral:
        raise ValueError("at least one rating is required")
    _check(ratings)
    _check(bilateral)
    if len(bilateral) == 1:
        raise ValueError("the bilateral factor needs ratings on both sides (at least two)")

    out: dict = {"citation": CITATION, "bilateral_factor_applied": bool(bilateral)}
    values = list(ratings)
    if bilateral:
        b_ordered, b_steps = _combine(bilateral)
        b_combined = b_steps[-1]
        factor_tenths = b_combined  # 10% of the combined value, in tenths of a percent
        b_value = (10 * b_combined + factor_tenths + 5) // 10  # combined + 10%, rounded half-up
        out["bilateral"] = {"ratings": b_ordered, "steps": b_steps, "combined_value": b_combined,
                            "factor_tenths": factor_tenths, "value_with_factor": b_value,
                            "citation": BILATERAL_CITATION}
        values.append(b_value)
    ordered, steps = _combine(values)
    combined = steps[-1]
    out.update({
        "ratings": ordered,
        "steps": steps,
        "combined_value": combined,
        "combined_rating": min((combined + 5) // 10 * 10, 100),
    })
    return out
