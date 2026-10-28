"""Load the Benefit Vault registry and enforce its pins.

The registry (``data/reference/benefit_vault_registry.json``) is the single
runtime source. Loading it checks, independently of the JSON Schema:

* the integrity stamp over the canonical JSON;
* every agent manifest has ``may_issue_determinations`` false;
* exactly one agent, ``benefit_vault_agent``, may pull from other agents;
* an agent exposes a fact only at the catalog's class, never above V2 and
  never a session-only fact;
* every rule compiles to the stored canonical spelling, every record's
  content hash matches, and no generated record claims VERIFIED.

VERIFIED marks come only from named-reviewer reviews (gate G1), applied with
``with_reviews``; a review counts only while the record's content hash is the
one the reviewer saw. The reviewer is named by a roster handle
(``vocab.REVIEWER_HANDLE``), never by a personal name or email address.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from . import ENGINE_NAME, REGISTRY_NAME, VAULT_AGENT_ID
from .canonical import canonical_json, sha256_hex
from .facts import CATALOG, catalog_view
from .rules import Node, compile_rule, tokens
from .vocab import NEVER_PULLABLE, OUTCOMES, RECORD_STATUSES, REVIEWER_HANDLE

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PATH = ROOT / "data" / "reference" / "benefit_vault_registry.json"
SCHEMA_PATH = ROOT / "schemas" / "json" / "benefit_vault_registry.schema.json"


class RegistryError(RuntimeError):
    """The registry failed a pin; the vault must not start."""


@dataclass(frozen=True)
class Benefit:
    benefit_id: str
    jurisdiction: str
    category: str
    title: str
    groups: Tuple[str, ...]
    rule: str
    node: Node = field(compare=False, repr=False)
    who_it_is_for: str
    value: str
    official_url: str
    official_url_status: str
    official_url_tier: int
    kind: str
    source_id: str
    source_tier: int
    record_status: str
    page_part: str
    ledger_ref: str
    content_hash: str
    lead_ids: Tuple[str, ...]
    caveat_ids: Tuple[str, ...]
    verified_by: Optional[str] = None
    verified_on: Optional[str] = None


@dataclass(frozen=True)
class Review:
    benefit_id: str
    verified_by: str
    verified_on: str
    content_hash: str


def _verify_integrity(data: Mapping) -> None:
    stamp = data.get("integrity") or {}
    body = {k: v for k, v in data.items() if k != "integrity"}
    if stamp.get("algorithm") != "sha256" or stamp.get("sha256") != sha256_hex(canonical_json(body)):
        raise RegistryError("registry integrity stamp does not match its content")


def _verify_agents(agents: Iterable[Mapping]) -> None:
    pullers = []
    for agent in agents:
        agent_id = agent.get("agent_id")
        if agent.get("may_issue_determinations") is not False:
            raise RegistryError(f"agent {agent_id} is not pinned to may_issue_determinations = false")
        if agent.get("may_pull_from_agents") is True:
            pullers.append(agent_id)
        elif agent.get("may_pull_from_agents") is not False:
            raise RegistryError(f"agent {agent_id} has no may_pull_from_agents flag")
        for item in agent.get("exposes", ()):
            spec = CATALOG.get(item["fact_key"])
            if spec is None:
                raise RegistryError(f"agent {agent_id} exposes unknown fact {item['fact_key']}")
            if item["data_class"] != spec.data_class or spec.data_class in NEVER_PULLABLE or not spec.pullable:
                raise RegistryError(f"agent {agent_id} may not expose {item['fact_key']} as {item['data_class']}")
    if pullers != [VAULT_AGENT_ID]:
        raise RegistryError(f"only {VAULT_AGENT_ID} may pull from agents; found {pullers}")


def _benefit(item: Mapping) -> Benefit:
    node, canonical = compile_rule(item["rule"])
    if canonical != item["rule"]:
        raise RegistryError(f"{item['benefit_id']}: stored rule is not canonical")
    if sorted({t.render() for t in tokens(node)}) != list(item["rule_tokens"]):
        raise RegistryError(f"{item['benefit_id']}: rule_tokens do not match the rule")
    content = {k: item[k] for k in ("jurisdiction", "category", "title", "groups", "rule", "who_it_is_for",
                                    "value", "official_url")}
    if sha256_hex(content) != item["content_hash"]:
        raise RegistryError(f"{item['benefit_id']}: content hash does not match")
    if item["record_status"] == "VERIFIED" or item["record_status"] not in RECORD_STATUSES:
        raise RegistryError(f"{item['benefit_id']}: generated records cannot be {item['record_status']}")
    return Benefit(
        benefit_id=item["benefit_id"], jurisdiction=item["jurisdiction"], category=item["category"],
        title=item["title"], groups=tuple(item["groups"]), rule=item["rule"], node=node,
        who_it_is_for=item["who_it_is_for"], value=item["value"], official_url=item["official_url"],
        official_url_status=item["official_url_status"], official_url_tier=item["official_url_tier"],
        kind=item["kind"], source_id=item["source_id"], source_tier=item["source_tier"],
        record_status=item["record_status"], page_part=item["page_part"], ledger_ref=item["ledger_ref"],
        content_hash=item["content_hash"], lead_ids=tuple(item["lead_ids"]), caveat_ids=tuple(item["caveat_ids"]),
    )


class VaultRegistry:
    def __init__(self, data: Mapping, *, check_schema: bool = True):
        if data.get("registry") != REGISTRY_NAME:
            raise RegistryError("not a Benefit Vault registry")
        _verify_integrity(data)
        if check_schema:
            self._check_schema(data)
        if list(data["vocabulary"]["outcomes"]) != list(OUTCOMES):
            raise RegistryError("registry outcomes differ from the v6 outcome set in code")
        if data["facts"] != catalog_view():
            raise RegistryError("registry fact catalog differs from the code catalog")
        _verify_agents(data["governance"]["agents"])
        self.data = data
        self.sha256 = data["integrity"]["sha256"]
        self.version = data["version"]
        self.as_of = data["as_of"]
        self.notice = data["notice"]
        self.caveats: Dict[str, str] = dict(data["caveats"])
        self.governance = data["governance"]
        self.sources: Dict[str, dict] = {s["source_id"]: s for s in data["sources"]}
        self.jurisdictions: Dict[str, dict] = {j["code"]: j for j in data["jurisdictions"]}
        self.rule_leads: Dict[str, dict] = {lead["lead_id"]: lead for lead in data["rule_leads"]}
        self.recovered_leads: List[dict] = list(data["recovered_leads"])
        self.benefits: Dict[str, Benefit] = {}
        for item in data["benefits"]:
            benefit = _benefit(item)
            if benefit.source_id not in self.sources:
                raise RegistryError(f"{benefit.benefit_id}: unknown source {benefit.source_id}")
            if set(benefit.lead_ids) - set(self.rule_leads):
                raise RegistryError(f"{benefit.benefit_id}: unknown rule lead")
            if set(benefit.caveat_ids) - set(self.caveats):
                raise RegistryError(f"{benefit.benefit_id}: unknown caveat")
            self.benefits[benefit.benefit_id] = benefit
        self.stale_reviews: Tuple[str, ...] = ()
        self._index()

    def _index(self) -> None:
        self.by_jurisdiction: Dict[str, List[Benefit]] = {}
        for benefit in self.benefits.values():
            self.by_jurisdiction.setdefault(benefit.jurisdiction, []).append(benefit)
        for items in self.by_jurisdiction.values():
            items.sort(key=lambda b: b.benefit_id)

    @staticmethod
    def _check_schema(data: Mapping) -> None:
        import jsonschema

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(data))
        if errors:
            first = errors[0]
            raise RegistryError(f"registry fails its schema: {first.message} ({len(errors)} errors)")

    @classmethod
    def load(cls, path: Path = DEFAULT_PATH, *, check_schema: bool = True) -> "VaultRegistry":
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RegistryError(f"cannot read registry: {exc}") from None
        return cls(data, check_schema=check_schema)

    @property
    def agents(self) -> List[dict]:
        return list(self.governance["agents"])

    def publish_policy(self, environment: Optional[str] = None) -> str:
        policy = self.governance["publish_policy"]
        env = environment or os.environ.get("VETBUDDY_ENV") or policy["default_environment"]
        return policy["environments"].get(env, policy["environments"][policy["default_environment"]])

    def with_reviews(self, reviews: Iterable[Review]) -> "VaultRegistry":
        """A copy with named-reviewer VERIFIED marks applied where content is unchanged."""
        clone = object.__new__(VaultRegistry)
        clone.__dict__.update(self.__dict__)
        clone.benefits = dict(self.benefits)
        stale = []
        for review in reviews:
            benefit = clone.benefits.get(review.benefit_id)
            if (benefit is None or not isinstance(review.verified_by, str)
                    or not re.fullmatch(REVIEWER_HANDLE, review.verified_by)
                    or review.content_hash != benefit.content_hash):
                stale.append(review.benefit_id)
                continue
            clone.benefits[review.benefit_id] = replace(benefit, record_status="VERIFIED",
                                                        verified_by=review.verified_by, verified_on=review.verified_on)
        clone.stale_reviews = tuple(sorted(set(stale)))
        clone._index()
        return clone

    def describe(self) -> dict:
        return {
            "engine": ENGINE_NAME,
            "registry": REGISTRY_NAME,
            "version": self.version,
            "as_of": self.as_of,
            "sha256": self.sha256,
            "counts": self.data["counts"],
        }


_CACHE: Dict[str, VaultRegistry] = {}


def default_registry() -> VaultRegistry:
    """The registry at the default path, loaded once per process."""
    key = str(DEFAULT_PATH)
    if key not in _CACHE:
        _CACHE[key] = VaultRegistry.load(DEFAULT_PATH)
    return _CACHE[key]
