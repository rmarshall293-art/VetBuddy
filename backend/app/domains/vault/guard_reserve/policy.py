"""Load and check the Guard & Reserve policy and the Operation Sentinel dataset.

Both files are authored inputs. Loading refuses them unless they agree with
each other and with the vault: every derived value is a value the vault's
fact catalog allows, every caveat a derivation names exists, every lead check
names a lead the vault registry carries, every selection token and category
is in the vault's vocabulary, and the role is the one named in the vault's
agent manifests.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, Mapping, Optional, Tuple

import yaml

from .. import VAULT_AGENT_ID
from ..facts import CATALOG, validate_value
from ..rules import TOKEN_NAMES
from ..vocab import BUILD_STATUSES, CATEGORIES, GROUPS
from . import ROLE_ID

ROOT = Path(__file__).resolve().parents[5]
POLICY_PATH = ROOT / "config" / "guard_reserve_vault_policy.yaml"

DERIVABLE_KEYS = frozenset({"component", "service_status", "on_active_duty_orders"})


class PolicyError(RuntimeError):
    """The Guard & Reserve policy or dataset is inconsistent; the role refuses to start."""


@dataclass(frozen=True)
class Status:
    status_id: str
    label: str
    sub: str
    selected_reserve: bool
    fta_eligible: bool
    guard_only: bool


@dataclass(frozen=True)
class Authority:
    authority_id: str
    citation: str
    label: str
    qualifies_ch33: bool
    tier_caveat: bool
    guard_only: bool
    coast_guard_only: bool


@dataclass(frozen=True)
class Component:
    component_id: str
    label: str
    short: str
    guard: bool
    coast_guard: bool


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GuardReservePolicy:
    def __init__(self, policy: Mapping[str, Any], dataset: Mapping[str, Any], *, policy_sha256: str = "",
                 dataset_sha256: str = ""):
        self.raw = policy
        self.version = str(policy["version"])
        self.as_of = str(policy["as_of"])
        self.policy_sha256 = policy_sha256
        self.dataset_sha256 = dataset_sha256
        if policy.get("role_id") != ROLE_ID:
            raise PolicyError(f"role_id must be {ROLE_ID}")
        if policy.get("parent_agent") != VAULT_AGENT_ID:
            raise PolicyError(f"parent_agent must be {VAULT_AGENT_ID}, the only agent that may pull")

        self.dataset_version = str(dataset["version"])
        self.governing_rule = str(dataset["governing_rule"])
        derivation = policy["derivation"]
        by_component = derivation["component_by_gr_component"]
        components = {}
        for item in dataset["components"]:
            if item.get("civilian"):
                continue        # DoD civilians: civilian employment alone creates no Guard/Reserve status
            cid = item["id"]
            if cid not in by_component:
                raise PolicyError(f"component {cid} has no vault component")
            validate_value("component", by_component[cid])
            components[cid] = Component(cid, item["label"], item["short"], by_component[cid] == "guard",
                                        bool(item.get("coast_guard")))
        if set(by_component) - set(components):
            raise PolicyError("the policy names a component the dataset does not have")
        self.components: Dict[str, Component] = components

        statuses = {}
        for item in dataset["statuses"]:
            if item.get("civilian_only"):
                continue
            statuses[item["id"]] = Status(item["id"], item["label"], item["sub"], bool(item.get("selected_reserve")),
                                          bool(item.get("fta_eligible")), bool(item.get("guard_only")))
        self.statuses: Dict[str, Status] = statuses
        self.caveats: Dict[str, str] = {k: " ".join(str(v).split()) for k, v in policy["caveats"].items()}

        self.derivation: Dict[str, Dict[str, Any]] = {}
        by_status = derivation["by_duty_status"]
        if set(by_status) != set(statuses):
            raise PolicyError("every Sentinel duty status needs exactly one derivation")
        for sid, entry in by_status.items():
            facts = {k: v for k, v in entry.items() if k != "caveats"}
            if set(facts) - DERIVABLE_KEYS:
                raise PolicyError(f"{sid} derives a fact the role may not derive")
            for key, value in facts.items():
                validate_value(key, value)
            for cid in entry.get("caveats", ()):
                if cid not in self.caveats:
                    raise PolicyError(f"{sid} names unknown caveat {cid}")
            self.derivation[sid] = {"facts": facts, "caveats": tuple(entry.get("caveats", ()))}

        targets = derivation["caveat_targets"]
        named = {c for entry in self.derivation.values() for c in entry["caveats"]}
        if set(targets) != named or not set(targets.values()) <= DERIVABLE_KEYS:
            raise PolicyError("every status caveat needs exactly one target fact the role derives")
        self.caveat_targets: Dict[str, str] = dict(targets)

        self.authorities: Dict[str, Authority] = {
            item["id"]: Authority(item["id"], item["citation"], item["label"], bool(item["qualifies_ch33"]),
                                  bool(item.get("tier_caveat")), bool(item.get("guard_only")),
                                  bool(item.get("coast_guard_only")))
            for item in dataset["authorities"]
        }

        selection = policy["selection"]
        self.select_groups: FrozenSet[str] = frozenset(selection["groups"])
        self.select_categories: FrozenSet[str] = frozenset(selection["categories"])
        self.select_tokens: FrozenSet[str] = frozenset(selection["rule_tokens"])
        self.lead_prefix: str = selection["lead_prefix"]
        if not self.select_groups <= set(GROUPS):
            raise PolicyError("selection names an unknown group")
        if not self.select_categories <= set(CATEGORIES):
            raise PolicyError("selection names an unknown category")
        if not self.select_tokens <= TOKEN_NAMES:
            raise PolicyError("selection names an unknown rule token")

        self.lead_checks: Dict[str, Dict[str, Any]] = dict(policy["lead_checks"])
        self.questions: Dict[str, str] = {k: " ".join(v["question"].split()) for k, v in policy["facts"].items()}
        days = policy["facts"]["qualifying_days"]
        self.days_range: Tuple[int, int] = (int(days["low"]), int(days["high"]))
        self.research_gaps = [dict(g) for g in policy["research_gaps"]]
        self.components_status = [dict(c) for c in policy["components"]]
        for item in self.research_gaps + self.components_status:
            if item["status"] not in BUILD_STATUSES:
                raise PolicyError(f"{item['id']}: unknown build status {item['status']}")
        for gap in self.research_gaps:
            if not set(gap["groups"]) <= set(GROUPS):
                raise PolicyError(f"{gap['id']}: unknown group")
        for key in self.questions:
            if key in CATALOG:
                raise PolicyError(f"{key} is a vault fact; Guard & Reserve answers use their own names")

    def check_against(self, registry) -> None:
        """The role and the vault registry must agree; called when the role is built."""
        if registry.governance is None:  # pragma: no cover - defensive
            raise PolicyError("registry has no governance block")
        manifest = next((a for a in registry.agents if a["agent_id"] == ROLE_ID), None)
        if manifest is None:
            raise PolicyError(f"no manifest for {ROLE_ID} in the vault registry: no manifest, no access")
        if manifest["may_pull_from_agents"] or manifest["may_issue_determinations"] or manifest["exposes"]:
            raise PolicyError(f"{ROLE_ID} may not pull, decide or expose facts")
        for lead_id in self.lead_checks:
            if lead_id not in registry.rule_leads:
                raise PolicyError(f"lead check {lead_id} names a lead the registry does not carry")
        for gap in self.research_gaps:
            missing = [r for r in gap.get("records", ()) if r not in registry.benefits]
            if missing:
                raise PolicyError(f"{gap['id']} names records the registry does not carry: {missing}")

    @classmethod
    def load(cls, policy_path: Path = POLICY_PATH, dataset_path: Optional[Path] = None) -> "GuardReservePolicy":
        policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        dataset_path = dataset_path or ROOT / policy["dataset"]
        dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
        return cls(policy, dataset, policy_sha256=_sha256_file(policy_path), dataset_sha256=_sha256_file(dataset_path))

    def catalog(self) -> dict:
        """Vocabulary for screens and other agents: what the role asks and what each answer means."""
        return {
            "role": {"role_id": ROLE_ID, "parent_agent": VAULT_AGENT_ID, "policy_version": self.version,
                     "policy_sha256": self.policy_sha256, "dataset_version": self.dataset_version,
                     "dataset_sha256": self.dataset_sha256},
            "governing_rule": self.governing_rule,
            "questions": [{"fact_key": k, "question": q, "data_class": "V1"} for k, q in self.questions.items()],
            "components": [{"id": c.component_id, "label": c.label, "short": c.short, "guard": c.guard}
                           for c in self.components.values()],
            "duty_statuses": [{"id": s.status_id, "label": s.label, "sub": s.sub,
                               "selected_reserve": s.selected_reserve, "guard_only": s.guard_only,
                               "derives": self.derivation[s.status_id]["facts"]}
                              for s in self.statuses.values()],
            "authorities": [{"id": a.authority_id, "citation": a.citation, "label": a.label,
                             "counts_toward_post_9_11_gi_bill": a.qualifies_ch33, "tier_caveat": a.tier_caveat,
                             "guard_only": a.guard_only, "coast_guard_only": a.coast_guard_only}
                            for a in self.authorities.values()],
            "research_gaps": self.research_gaps,
            "components_status": self.components_status,
        }


_DEFAULT: Optional[GuardReservePolicy] = None


def default_policy() -> GuardReservePolicy:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = GuardReservePolicy.load()
    return _DEFAULT
