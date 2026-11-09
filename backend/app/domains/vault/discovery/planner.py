"""Discovery planner: what to research next, as V0-only search queries.

The planner looks for gaps in the registry (a jurisdiction with no source, a
page with an unread tail, a state category with no record) and turns each gap
into a search query built by the egress guard from fixed templates and fixed
vocabulary. It never sees a person's facts.

The planner only plans. Running a query needs a search endpoint, and the
registry lists none (``governance.discovery.search_endpoints`` is empty), so
execution is BLOCKED until a hosting decision names one. A result on a host
that is not on the allowlist can be proposed for review but never fetched.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from ..canonical import sha256_hex
from ..vocab import CATEGORY_LABELS, JURISDICTIONS, STATE_CATEGORIES
from .. import registry as registry_module
from ..governance.egress import EgressGuard


@dataclass(frozen=True)
class DiscoveryTask:
    task_id: str
    reason: str               # NO_SOURCE, TAIL_UNREAD, CATEGORY_GAP
    jurisdiction: str
    category: Optional[str]
    template_id: str
    query: str

    def view(self) -> dict:
        return dict(self.__dict__)


class DiscoveryPlanner:
    def __init__(self, registry: "registry_module.VaultRegistry", egress: EgressGuard):
        self.registry = registry
        self.egress = egress

    def gaps(self) -> List[Tuple[str, str, Optional[str]]]:
        """(reason, jurisdiction, category) in priority order."""
        found: List[Tuple[str, str, Optional[str]]] = []
        for code, entry in self.registry.jurisdictions.items():
            if code != "US" and entry["coverage"] == "SOURCE_NOT_AVAILABLE":
                found.append(("NO_SOURCE", code, None))
        for code, entry in self.registry.jurisdictions.items():
            if code != "US" and entry["tail_unread_chars"]:
                found.append(("TAIL_UNREAD", code, None))
        for code in sorted(JURISDICTIONS):
            if code == "US" or self.registry.jurisdictions[code]["coverage"] != "COVERED":
                continue
            present = {b.category for b in self.registry.by_jurisdiction.get(code, ())}
            for category in STATE_CATEGORIES:
                if category != "OTHER" and category not in present:
                    found.append(("CATEGORY_GAP", code, category))
        return found

    def plan(self, *, reasons: Optional[Sequence[str]] = None, limit: int = 200) -> List[DiscoveryTask]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit is 1-1000")
        tasks: List[DiscoveryTask] = []
        for reason, code, category in self.gaps():
            if reasons and reason not in reasons:
                continue
            name = JURISDICTIONS[code]
            if category is None:
                plans = [("jur_cat_vet", "other benefits"), ("jur_cat_guard", "National Guard tuition")]
            else:
                plans = [("jur_cat_vet", CATEGORY_LABELS[category])]
            for template_id, label in plans:
                query = self.egress.build_query(template_id, jurisdiction=name, category=label)
                task_id = "disc." + sha256_hex(f"{reason}|{code}|{category}|{template_id}")[:16]
                tasks.append(DiscoveryTask(task_id, reason, code, category, template_id, query))
                if len(tasks) >= limit:
                    return tasks
        return tasks

    @property
    def executable(self) -> bool:
        return bool(self.registry.governance["discovery"]["search_endpoints"])
