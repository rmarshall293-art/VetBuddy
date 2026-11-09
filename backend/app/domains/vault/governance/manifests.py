"""Agent manifests: who may hold, expose and pull what.

No manifest means no access. The pins are enforced four ways: the JSON
Schema, this loader (and the registry loader), the database CHECK constraints
in migration 0014, and the tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Mapping, Optional, Tuple

from .. import VAULT_AGENT_ID
from ..facts import CATALOG
from ..vocab import DATA_CLASSES, NEVER_PULLABLE


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class Exposure:
    fact_key: str
    data_class: str


@dataclass(frozen=True)
class Manifest:
    agent_id: str
    name: str
    plane: int
    role: str
    may_pull_from_agents: bool
    highest_class_held: str
    exposes: Tuple[Exposure, ...]
    may_issue_determinations: bool = False

    def exposure(self, fact_key: str) -> Optional[Exposure]:
        for item in self.exposes:
            if item.fact_key == fact_key:
                return item
        return None

    @property
    def exposed_keys(self) -> FrozenSet[str]:
        return frozenset(item.fact_key for item in self.exposes)


def _manifest(item: Mapping) -> Manifest:
    agent_id = item.get("agent_id")
    if item.get("may_issue_determinations") is not False:
        raise ManifestError(f"{agent_id}: may_issue_determinations must be false")
    pull = item.get("may_pull_from_agents")
    if not isinstance(pull, bool):
        raise ManifestError(f"{agent_id}: may_pull_from_agents must be true or false")
    if pull and agent_id != VAULT_AGENT_ID:
        raise ManifestError(f"{agent_id}: only {VAULT_AGENT_ID} may pull from other agents")
    held = item.get("highest_class_held")
    if held not in DATA_CLASSES:
        raise ManifestError(f"{agent_id}: unknown class {held}")
    exposes = []
    for entry in item.get("exposes", ()):
        key, data_class = entry.get("fact_key"), entry.get("data_class")
        spec = CATALOG.get(key)
        if spec is None:
            raise ManifestError(f"{agent_id}: exposes unknown fact {key}")
        if data_class != spec.data_class:
            raise ManifestError(f"{agent_id}: {key} is {spec.data_class}, not {data_class}")
        if data_class in NEVER_PULLABLE or not spec.pullable or spec.session_only:
            raise ManifestError(f"{agent_id}: {key} ({data_class}) may never travel between agents")
        if DATA_CLASSES.index(data_class) > DATA_CLASSES.index(held):
            raise ManifestError(f"{agent_id}: exposes {key} above the class it holds")
        exposes.append(Exposure(key, data_class))
    if pull and exposes:
        raise ManifestError(f"{agent_id}: the pulling agent exposes nothing")
    return Manifest(agent_id=agent_id, name=item["name"], plane=int(item["plane"]), role=item["role"],
                    may_pull_from_agents=pull, highest_class_held=held,
                    exposes=tuple(sorted(exposes, key=lambda e: e.fact_key)))


class ManifestSet:
    def __init__(self, items: Iterable[Mapping]):
        self._by_id: Dict[str, Manifest] = {}
        for item in items:
            manifest = _manifest(item)
            if manifest.agent_id in self._by_id:
                raise ManifestError(f"duplicate manifest {manifest.agent_id}")
            self._by_id[manifest.agent_id] = manifest
        pullers = [m.agent_id for m in self._by_id.values() if m.may_pull_from_agents]
        if pullers != [VAULT_AGENT_ID]:
            raise ManifestError(f"exactly one agent may pull ({VAULT_AGENT_ID}); found {pullers}")

    @classmethod
    def from_registry(cls, registry) -> "ManifestSet":
        return cls(registry.agents)

    def get(self, agent_id: str) -> Optional[Manifest]:
        return self._by_id.get(agent_id)

    def all(self) -> List[Manifest]:
        return [self._by_id[k] for k in sorted(self._by_id)]

    def sources_for(self, fact_key: str) -> List[str]:
        return sorted(m.agent_id for m in self._by_id.values() if fact_key in m.exposed_keys)

    def public_view(self) -> List[dict]:
        return [
            {
                "agent_id": m.agent_id, "name": m.name, "plane": m.plane, "role": m.role,
                "may_issue_determinations": m.may_issue_determinations,
                "may_pull_from_agents": m.may_pull_from_agents,
                "highest_class_held": m.highest_class_held,
                "exposes": [{"fact_key": e.fact_key, "data_class": e.data_class} for e in m.exposes],
            }
            for m in self.all()
        ]
