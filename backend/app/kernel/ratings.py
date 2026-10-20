"""Combined disability rating arithmetic, 38 CFR 4.25 (educational only).

Integer arithmetic throughout (defect A-01 was float + banker's rounding): each
Table I step rounds half-up to a whole number, and the combined value is
converted to the nearest 10 exactly once, with 5s rounding up. The bilateral
factor (38 CFR 4.26) is NOT applied (gap A-03) and the result says so.

This is arithmetic on numbers the user enters, never a prediction of what VA
will rate (governance §5). frontend/src/kernel.js mirrors it; the parity test
proves they agree.
"""

from __future__ import annotations

CITATION = "38 CFR 4.25"


def combine_ratings(ratings: list[int]) -> dict:
    if not ratings:
        raise ValueError("at least one rating is required")
    for r in ratings:
        if isinstance(r, bool) or not isinstance(r, int) or r < 0 or r > 100 or r % 10:
            raise ValueError("each rating must be a whole multiple of 10 from 0 to 100")
    ordered = sorted(ratings, reverse=True)
    combined = ordered[0]
    steps = [combined]
    for r in ordered[1:]:
        num = (100 - combined) * r
        combined += (2 * num + 100) // 200  # num/100 rounded half-up, in integers
        steps.append(combined)
    return {
        "ratings": ordered,
        "steps": steps,
        "combined_value": combined,
        "combined_rating": min((combined + 5) // 10 * 10, 100),
        "citation": CITATION,
        "bilateral_factor_applied": False,
    }
