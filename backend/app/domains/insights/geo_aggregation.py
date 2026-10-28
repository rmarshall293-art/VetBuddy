"""Geographic aggregation with k-anonymity suppression ("awareness of area needs").

Integrated from the consent package's ``consent/geographic_aggregation.py``
(2026-10-27 upload; the rest of that package, consent_enforcement.py,
test_consent.py and consent_schema.sql, was not supplied: SOURCE_NOT_AVAILABLE).

Status: this module is IMPLEMENTED_TESTED as a pure kernel. The feature is
PLANNED: VetBuddy stores no county, and no ``geographic_insight`` consent
purpose exists yet (adding one, and a county field, are decisions recorded in
docs/GAP_MATRIX.md). Nothing calls it with real data. Re-identifying
aggregates is a foreclosed consent purpose (migration 0010).

Why it exists. VetBuddy holds branch, component and service details. In a
rural county with three users, "one E-6 with a 0411 MOS, 12 years of service"
is a person, not a statistic. So no figure about a group smaller than k is
released, at the query layer, so an analyst cannot export an identifying cell.

Rules (as received):
  * k = 11, a floor in code; a lower k is refused.
  * Only listed dimensions may be aggregated; a deny list catches health,
    rating and high-cardinality fields even if someone widens the allow list.
  * A suppressed cell carries no count, range or estimate.
  * Cross-tab cells are checked one by one.

Defects fixed on integration (each has a test in tests/test_geo_aggregation.py):
  GA-01  A one-dimension report with exactly one suppressed cell leaked it by
         subtraction whenever the total was also published (the state report
         publishes ``total_consented_users``). Complementary suppression now
         applies to one-dimension aggregates too.
  GA-02  Cross-tabs guarded rows only. A column with one suppressed cell was
         recoverable from the column margin (the state report publishes
         ``by_career_cluster``). Rows and columns are now both guarded,
         repeated until stable, because each extra suppression can create a
         new weak line.
  GA-05  The received guard acted only on exactly one suppressed cell. Two
         withheld cells holding 3 and 4 people still released "7 people across
         these two groups" by subtraction. The rule is now the standard one:
         in any line whose total is or may be published, keep withholding the
         smallest released cell until the withheld cells together hold at
         least k people (or nothing is released).
  GA-03  A suppressed key still discloses that the group is non-empty. With a
         ``domain`` (every possible key, e.g. all counties of a state), empty
         groups are reported as suppressed too, so "suppressed" no longer
         implies "at least one". Without a domain the report says so.
  GA-04  ``total_consented_users`` could be released while every cell was
         suppressed and the same report released a margin; the total now
         follows the same complementary rule as any other cell.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Optional

#: Minimum group size before any statistic is released. 11 is a common
#: public-health reporting floor, above the k=5 seen elsewhere; the population
#: here is small and tightly networked.
DEFAULT_K_THRESHOLD = 11

#: Fields that may appear in a geographic aggregate. Anything else is refused,
#: so adding a dimension is a deliberate act.
PERMITTED_AGGREGATE_DIMENSIONS = frozenset({
    "state_code", "county_fips", "branch", "years_of_service_band", "top_career_cluster",
    "education_gap_category", "referral_category",
})

#: Never allowed, even if added to the permitted set by mistake.
FORBIDDEN_AGGREGATE_DIMENSIONS = frozenset({
    "disability_rating", "combined_rating", "va_rating", "diagnostic_code", "diagnosis", "condition",
    "wellness_band", "phq9_total", "gad7_total", "pcl5_total", "moral_injury_score",
    "occupation_code",   # MOS is high-cardinality and identifying
    "pay_grade",         # crossed with county, narrows to individuals
    "afqt_percentile", "account_id", "user_id", "tenant_id", "zip_code", "street_address",
    "latitude", "longitude",
})

SUPPRESSION_NOTE = ("Groups smaller than {k} are withheld entirely. No count, range or estimate is given for a "
                    "withheld group, since a range still identifies someone when the true value is one or two. "
                    "A withheld group is NOT a zero.")
PRESENCE_NOTE = ("Without a complete list of possible groups, a withheld group shows that at least one consented "
                 "user is in it. Pass a domain to withhold empty groups too.")


class AggregationError(ValueError):
    """An invalid or unsafe aggregation request."""


@dataclass(frozen=True)
class SuppressedCell:
    reason: str

    def to_dict(self) -> dict:
        return {"suppressed": True, "reason": self.reason, "count": None}


SMALL = "fewer than {k} veterans in this group, or none"
COMPLEMENT = "withheld so another withheld group cannot be worked out by subtraction"


@dataclass
class GeographicAggregate:
    dimension: str
    k_threshold: int
    released: dict
    suppressed: dict
    domain_complete: bool = False

    def to_dict(self) -> dict:
        notes = [SUPPRESSION_NOTE.format(k=self.k_threshold)]
        if not self.domain_complete:
            notes.append(PRESENCE_NOTE)
        return {"dimension": self.dimension, "k_threshold": self.k_threshold, "released": dict(self.released),
                "suppressed": {k: v.to_dict() for k, v in self.suppressed.items()},
                "suppression_note": " ".join(notes)}

    def total_released(self) -> int:
        return sum(self.released.values())


def validate_dimension(dimension: str) -> None:
    if dimension in FORBIDDEN_AGGREGATE_DIMENSIONS:
        raise AggregationError(f"'{dimension}' may never appear in a geographic aggregate: it is health or rating "
                               "data, or identifying when crossed with county.")
    if dimension not in PERMITTED_AGGREGATE_DIMENSIONS:
        raise AggregationError(f"'{dimension}' is not a permitted aggregate dimension. Permitted: "
                               f"{sorted(PERMITTED_AGGREGATE_DIMENSIONS)}. Add one deliberately after considering "
                               "re-identification risk, not by loosening this check.")


def _check_k(k_threshold: int) -> None:
    if not isinstance(k_threshold, int) or k_threshold < DEFAULT_K_THRESHOLD:
        raise AggregationError(f"k_threshold {k_threshold!r} is below the floor of {DEFAULT_K_THRESHOLD}. Lowering it "
                               "to make a report look complete defeats the purpose of having one.")


def _protect_line(released: dict, suppressed: dict, counts: dict, k_threshold: int) -> list:
    """One line (a one-dimension report, or a row or column of a cross-tab) whose
    total is, or may be, published. Subtraction gives the sum of the withheld
    cells; while that sum is under k (and something is withheld), withhold the
    smallest released cell too (GA-01, GA-05). Returns the keys newly withheld."""
    moved = []
    while suppressed and released and sum(counts.get(key, 0) for key in suppressed) < k_threshold:
        smallest = min(sorted(released, key=str), key=lambda key: released[key])
        suppressed[smallest] = SuppressedCell(COMPLEMENT)
        del released[smallest]
        moved.append(smallest)
    return moved


def aggregate(records: Iterable[dict], dimension: str, k_threshold: int = DEFAULT_K_THRESHOLD,
              domain: Optional[Iterable] = None) -> GeographicAggregate:
    """Count ``records`` by ``dimension``, withholding any group below k.

    ``records`` must already be limited to people who consented to this use;
    this function sees no per-account data and does not check consent.
    """
    validate_dimension(dimension)
    _check_k(k_threshold)
    counts = Counter(r[dimension] for r in records if r.get(dimension) is not None)
    keys = set(counts)
    if domain is not None:
        domain = set(domain)
        unknown = keys - domain
        if unknown:
            raise AggregationError(f"values outside the domain: {sorted(map(str, unknown))}")
        keys = domain
    released, suppressed = {}, {}
    for key in sorted(keys, key=str):
        n = counts.get(key, 0)
        if n >= k_threshold:
            released[key] = n
        else:
            suppressed[key] = SuppressedCell(SMALL.format(k=k_threshold))
    _protect_line(released, suppressed, counts, k_threshold)                      # GA-01, GA-05
    return GeographicAggregate(dimension, k_threshold, released, suppressed, domain_complete=domain is not None)


def cross_tabulate(records: Iterable[dict], dimension_a: str, dimension_b: str,
                   k_threshold: int = DEFAULT_K_THRESHOLD) -> dict:
    """Two-dimensional aggregate, e.g. county by career cluster. Each cell is
    checked on its own, then rows and columns are both protected against
    recovery by subtraction from their margins, until nothing changes."""
    validate_dimension(dimension_a)
    validate_dimension(dimension_b)
    _check_k(k_threshold)
    if dimension_a == dimension_b:
        raise AggregationError("Cross-tabulation requires two distinct dimensions.")
    cells: Counter = Counter()
    for record in records:
        a, b = record.get(dimension_a), record.get(dimension_b)
        if a is not None and b is not None:
            cells[(a, b)] += 1
    released = {cell: n for cell, n in cells.items() if n >= k_threshold}
    suppressed = {cell: SuppressedCell(SMALL.format(k=k_threshold)) for cell, n in cells.items() if n < k_threshold}

    changed = True
    while changed:                                                                # GA-02
        changed = False
        for axis in (0, 1):
            for line in sorted({cell[axis] for cell in cells}, key=str):
                line_rel = {c: n for c, n in released.items() if c[axis] == line}
                line_sup = {c: s for c, s in suppressed.items() if c[axis] == line}
                for c in _protect_line(line_rel, line_sup, cells, k_threshold):
                    suppressed[c] = line_sup[c]
                    del released[c]
                    changed = True

    rows: dict = {}
    for (a, b), n in sorted(released.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        rows.setdefault(a, {"released": {}, "suppressed": {}})["released"][b] = n
    for (a, b), s in sorted(suppressed.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        rows.setdefault(a, {"released": {}, "suppressed": {}})["suppressed"][b] = s.to_dict()
    return {"dimensions": [dimension_a, dimension_b], "k_threshold": k_threshold, "rows": rows,
            "suppression_note": SUPPRESSION_NOTE.format(k=k_threshold) + " " + PRESENCE_NOTE}


def state_agency_report(records: Iterable[dict], state_code: str, k_threshold: int = DEFAULT_K_THRESHOLD,
                        county_domain: Optional[Iterable[str]] = None) -> dict:
    """What a state agency licensee would receive: county counts and career
    demand, all suppressed below k, never health data (none is stored).
    Not wired: no county field and no geographic_insight consent purpose exist."""
    _check_k(k_threshold)
    in_state = [r for r in records if r.get("state_code") == state_code]
    by_county = aggregate(in_state, "county_fips", k_threshold, domain=county_domain)
    # GA-04: the total is one more line total; publish it only if no single
    # county cell would then be recoverable (aggregate() already withheld a
    # complement), and only if it clears k itself.
    total = len(in_state) if len(in_state) >= k_threshold else None
    return {
        "state_code": state_code,
        "total_consented_users": total,
        "total_suppressed": total is None,
        "by_county": by_county.to_dict(),
        "by_career_cluster": aggregate(in_state, "top_career_cluster", k_threshold).to_dict(),
        "by_education_gap": aggregate(in_state, "education_gap_category", k_threshold).to_dict(),
        "county_by_cluster": cross_tabulate(in_state, "county_fips", "top_career_cluster", k_threshold),
        "methodology": {
            "k_threshold": k_threshold,
            "consent_basis": "Only veterans who granted the geographic insight purpose (not yet offered).",
            "suppression": SUPPRESSION_NOTE.format(k=k_threshold),
            "excluded_by_design": "No health, disability, wellness or claim data: VetBuddy does not store any, so "
                                  "there is nothing to aggregate.",
            "not_a_population_estimate": "These are consenting VetBuddy users, not all veterans in the county. Do "
                                         "not use them as a denominator for prevalence.",
        },
    }
