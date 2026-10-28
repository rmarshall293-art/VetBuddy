"""Keyword search over the vault.

Search needs no facts about the person and is safe in Mode A. The query is
the person's own words, so it passes the PII minimizer first and never leaves
the process: discovery queries are built only from fixed vocabulary (see
discovery.planner), never from this text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from .registry import Benefit, VaultRegistry
from .vocab import CATEGORY_LABELS, GROUP_LABELS, JURISDICTIONS

STOPWORDS = frozenset(
    "a an and any are as at be benefit benefits by can do does for from get how i in is it me my of on or our "
    "the to us we what where which who with you your".split()
)

# Everyday words mapped to categories so "park pass" or "hunting license"
# finds records whose titles use other words.
SYNONYMS: Dict[str, Tuple[str, ...]] = {
    "park": ("PARKS", "PASS"), "parks": ("PARKS", "PASS"), "pass": ("PASS", "PARKS"), "passes": ("PASS", "PARKS"),
    "camping": ("PARKS",), "museum": ("PASS",), "museums": ("PASS",),
    "hunting": ("HUNTFISH",), "fishing": ("HUNTFISH",), "hunt": ("HUNTFISH",), "fish": ("HUNTFISH",),
    "tuition": ("EDU", "GUARD_EDU", "SCHOLARSHIP"), "college": ("EDU", "GUARD_EDU", "SCHOLARSHIP"),
    "school": ("EDU", "SCHOLARSHIP"), "scholarship": ("SCHOLARSHIP", "EDU"), "scholarships": ("SCHOLARSHIP", "EDU"),
    "gi": ("EDU",), "education": ("EDU", "GUARD_EDU", "SCHOLARSHIP"),
    "ticket": ("TICKETS",), "tickets": ("TICKETS",), "concert": ("TICKETS",), "theme": ("TICKETS",),
    "discount": ("DEALS", "TICKETS", "TRAVEL"), "discounts": ("DEALS", "TICKETS", "TRAVEL"), "deal": ("DEALS",),
    "deals": ("DEALS",), "phone": ("DEALS",), "store": ("DEALS",),
    "travel": ("TRAVEL",), "flight": ("TRAVEL",), "flights": ("TRAVEL",), "hotel": ("TRAVEL", "MWR"),
    "vacation": ("TRAVEL", "MWR"), "resort": ("MWR",),
    "plate": ("PLATES",), "plates": ("PLATES",), "vehicle": ("PLATES",), "registration": ("PLATES",),
    "tax": ("INCTAX", "PROPTAX"), "taxes": ("INCTAX", "PROPTAX"), "property": ("PROPTAX",), "income": ("INCTAX",),
    "retirement": ("INCTAX",), "job": ("JOBS",), "jobs": ("JOBS",), "hiring": ("JOBS",), "employment": ("JOBS",),
    "cemetery": ("BURIAL",), "burial": ("BURIAL",), "funeral": ("BURIAL",),
    "home": ("HOMES", "HOUSING"), "homes": ("HOMES",), "nursing": ("HOMES",), "loan": ("HOUSING", "BONUS"),
    "mortgage": ("HOUSING", "BONUS"), "insurance": ("INSURANCE", "GUARD_PAY"), "health": ("HEALTH",),
    "grant": ("BONUS",), "grants": ("BONUS",), "emergency": ("BONUS",), "bonus": ("BONUS",),
    "license": ("LICENSE", "HUNTFISH"), "licensing": ("LICENSE",), "survivor": ("FAMILY",), "survivors": ("FAMILY",),
    "family": ("FAMILY",), "commissary": ("MWR",), "exchange": ("MWR",),
}

GROUP_WORDS: Dict[str, str] = {
    "guard": "ng", "reserve": "rsv", "reservist": "rsv", "veteran": "vet", "veterans": "vet", "retiree": "ret",
    "retirees": "ret", "retired": "ret", "spouse": "sp", "spouses": "sp", "child": "ch", "children": "ch",
    "kids": "ch", "widow": "ss", "widower": "ss", "disabled": "dv", "active": "ad", "gold": "gs",
}


def words(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


@dataclass(frozen=True)
class SearchQuery:
    text: str = ""
    jurisdictions: Optional[Tuple[str, ...]] = None
    categories: Optional[FrozenSet[str]] = None
    groups: Optional[FrozenSet[str]] = None
    kinds: Optional[FrozenSet[str]] = None
    limit: int = 25
    offset: int = 0


class Search:
    def __init__(self, registry: VaultRegistry):
        self.registry = registry
        self._index: Dict[str, Tuple[List[str], List[str], List[str]]] = {}
        for benefit in registry.benefits.values():
            title = words(benefit.title)
            labels = words(CATEGORY_LABELS[benefit.category]) + [w for g in benefit.groups for w in words(GROUP_LABELS[g])]
            body = words(f"{benefit.who_it_is_for} {benefit.value} {JURISDICTIONS[benefit.jurisdiction]}")
            self._index[benefit.benefit_id] = (title, labels, body)

    def _score(self, benefit: Benefit, terms: Sequence[str]) -> int:
        title, labels, body = self._index[benefit.benefit_id]
        score = 0
        for term in terms:
            score += 3 * title.count(term) + 2 * labels.count(term) + body.count(term)
            if benefit.category in SYNONYMS.get(term, ()):
                score += 2
            group = GROUP_WORDS.get(term)
            if group and group in benefit.groups:
                score += 1
        return score

    def run(self, query: SearchQuery) -> Tuple[List[Benefit], int]:
        if not 1 <= query.limit <= 100 or query.offset < 0:
            raise ValueError("limit is 1-100 and offset is 0 or more")
        if query.jurisdictions:
            bad = [c for c in query.jurisdictions if c not in JURISDICTIONS]
            if bad:
                raise ValueError(f"unknown jurisdiction {', '.join(bad)}")
        terms = words(query.text)
        scored = []
        for benefit in self.registry.benefits.values():
            if query.jurisdictions and benefit.jurisdiction not in query.jurisdictions:
                continue
            if query.categories and benefit.category not in query.categories:
                continue
            if query.groups and not (set(query.groups) & set(benefit.groups)):
                continue
            if query.kinds and benefit.kind not in query.kinds:
                continue
            score = self._score(benefit, terms) if terms else 1
            if score > 0:
                scored.append((-score, benefit.benefit_id, benefit))
        scored.sort(key=lambda row: (row[0], row[1]))
        total = len(scored)
        page = [row[2] for row in scored[query.offset:query.offset + query.limit]]
        return page, total
