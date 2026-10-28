"""Closed vocabularies for the Benefit Vault.

Every enumeration the vault uses lives here so the registry schema, the SQL
CHECK constraints and the Python code can be compared against one list. A
test reads the migration and asserts that each SQL CHECK names exactly these
values.

Words matter here. Outcomes are Master Prompt v6 outcomes: the vault never
says a person "is eligible" or "was approved". It reports what the encoded
rules say about the facts it was given, and points to the official source.
"""
from __future__ import annotations

from typing import Final

# Master Prompt v6 outcomes, in display order.
OUTCOMES: Final = (
    "PRELIMINARY_MATCH",
    "NEEDS_INFORMATION",
    "NEEDS_EVIDENCE",
    "DOES_NOT_MEET_ENCODED_RULES",
    "SOURCE_STALE",
    "CONFLICTING_AUTHORITY",
    "HUMAN_REVIEW_REQUIRED",
)

# v6 record status. VERIFIED needs a named human reviewer (gate G1).
RECORD_STATUSES: Final = (
    "UNVERIFIED",
    "SOURCE_CHECKED",
    "CONTESTED",
    "SUPERSEDED",
    "ILLUSTRATIVE",
    "HEURISTIC",
    "VERIFIED",
)

# A reviewer is recorded by a roster handle (lowercase letters, digits, dot,
# dash or underscore), never by a personal name or an email address. The same
# pattern is a CHECK on ref.vault_benefit.verified_by.
REVIEWER_HANDLE: Final = r"^[a-z0-9][a-z0-9._-]{1,63}$"

# v6 build status labels used in the component register.
BUILD_STATUSES: Final = (
    "IMPLEMENTED_TESTED",
    "IMPLEMENTED_UNVERIFIED",
    "PARTIAL",
    "MOCK",
    "PLANNED",
    "DISABLED",
    "BLOCKED",
    "SOURCE_NOT_AVAILABLE",
)

DATA_CLASSES: Final = ("V0", "V1", "V2", "V3", "V4", "V5")

# Privacy modes and the highest data class each may hold. Mode C has no
# ceiling because it cannot be reached in this build.
MODE_CEILING: Final = {"A": "V1", "B": "V2"}

# Classes that can never travel between agents. V3 and V5 are never pullable;
# V4 is never pulled (severe-disability flags stay session-only).
NEVER_PULLABLE: Final = frozenset({"V3", "V4", "V5"})

STATE_CATEGORIES: Final = (
    "INCTAX", "PROPTAX", "PLATES", "GUARD_EDU", "EDU", "JOBS", "GUARD_PAY",
    "HUNTFISH", "PARKS", "HOMES", "BURIAL", "BONUS", "OTHER",
)
FEDERAL_ONLY_CATEGORIES: Final = (
    "SCHOLARSHIP", "PASS", "TICKETS", "DEALS", "TRAVEL", "MWR", "HEALTH",
    "HOUSING", "INSURANCE", "FAMILY", "LICENSE",
)
CATEGORIES: Final = STATE_CATEGORIES + FEDERAL_ONLY_CATEGORIES

# Plain-language labels. These are also the only category words discovery
# queries may contain (see discovery.planner).
CATEGORY_LABELS: Final = {
    "INCTAX": "income tax relief",
    "PROPTAX": "property tax relief",
    "PLATES": "license plates and vehicle fees",
    "GUARD_EDU": "National Guard tuition",
    "EDU": "education and tuition",
    "JOBS": "jobs and hiring preference",
    "GUARD_PAY": "National Guard pay and insurance",
    "HUNTFISH": "hunting and fishing licenses",
    "PARKS": "state parks",
    "HOMES": "veterans homes and housing",
    "BURIAL": "burial and cemeteries",
    "BONUS": "bonuses, grants and emergency aid",
    "OTHER": "other benefits",
    "SCHOLARSHIP": "scholarships",
    "PASS": "park and museum passes",
    "TICKETS": "event and attraction tickets",
    "DEALS": "retail and service discounts",
    "TRAVEL": "travel",
    "MWR": "morale, welfare and recreation",
    "HEALTH": "health care",
    "HOUSING": "home loans and housing",
    "INSURANCE": "life insurance",
    "FAMILY": "family and survivor support",
    "LICENSE": "licensing and credentials",
}

GROUPS: Final = ("ad", "ng", "rsv", "vet", "dv", "ret", "sp", "ch", "ss", "gs", "sm", "all")
GROUP_LABELS: Final = {
    "ad": "active duty",
    "ng": "National Guard",
    "rsv": "Reserve",
    "vet": "veterans",
    "dv": "disabled veterans",
    "ret": "military retirees",
    "sp": "spouses",
    "ch": "children",
    "ss": "surviving spouses",
    "gs": "Gold Star families",
    "sm": "service members",
    "all": "everyone",
}

# Kinds of record. A commercial deal or a nonprofit program is never presented
# as a government benefit.
KINDS: Final = ("STATE_BENEFIT", "FEDERAL_BENEFIT", "NONPROFIT_PROGRAM", "COMMERCIAL_DEAL")

# How the vault knows what a record says.
PAGE_STATUSES: Final = ("OPENED", "SEEN_IN_SEARCH")
URL_STATUSES: Final = ("SAME_AS_SOURCE", "LINKED_FROM_SOURCE", "SEEN_IN_SEARCH")

# Source tiers.
#   1  the administering government body's own page, or official law text
#   2  an official summary or aggregator, or an unofficial copy of the law
#   3  the program operator's own page (nonprofit, association or vendor)
#   4  a secondary source or a recovered lead
TIERS: Final = (1, 2, 3, 4)

# Jurisdictions: the 50 states, DC, the five inhabited territories and US for
# federal records.
JURISDICTIONS: Final = {
    "US": "United States (federal)",
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia", "PR": "Puerto Rico", "VI": "U.S. Virgin Islands",
    "GU": "Guam", "MP": "Northern Mariana Islands", "AS": "American Samoa",
}
SUB_NATIONAL: Final = tuple(code for code in JURISDICTIONS if code != "US")

# The only purpose for which another agent's facts may be pulled.
PULL_PURPOSES: Final = ("benefit_matching",)

VAULT_EVENTS: Final = (
    "PULL_ALLOWED",
    "PULL_DENIED",
    "GRANT_CREATED",
    "GRANT_REVOKED",
)

# Reason codes the broker writes to the pull ledger. Codes, never values.
DENIAL_REASONS: Final = (
    "REQUESTER_NOT_PERMITTED",
    "NO_MANIFEST",
    "NOT_EXPOSED",
    "CLASS_NEVER_PULLABLE",
    "CLASS_ABOVE_MODE_CEILING",
    "NO_ACTIVE_GRANT",
    "GRANT_EXPIRED",
    "GRANT_REVOKED",
    "KEY_NOT_GRANTED",
    "PURPOSE_NOT_ALLOWED",
    "NOT_MINIMUM_NECESSARY",
    "SOURCE_UNAVAILABLE",
    "MODE_C_UNREACHABLE",
    "DURATION_NOT_ALLOWED",
)

ALLOW_REASON: Final = "ALLOWED"

# The person's own tracking of a saved benefit. VetBuddy files nothing, so
# "applied" always means the person applied with the agency or vendor.
SAVED_STATUSES: Final = ("INTERESTED", "GATHERING_DOCUMENTS", "APPLIED_ON_MY_OWN", "NOT_FOR_ME")
