"""The v6 response envelope.

Every vault response carries the common notice, the engine and registry
identity, the privacy mode and publish policy in force, and two hashes:
``inputs`` over everything that went in and ``output`` over everything that
came out. Two calls with equal inputs give equal output hashes; a test pins
that. ``determination`` is always "none": the vault reports what encoded
rules say and points to the official source.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from . import ENGINE_NAME, ENGINE_VERSION
from .canonical import sha256_hex
from .facts import FactSet
from .guards import LanguageGuard, OutputBlocked
from .registry import VaultRegistry

ENVELOPE_NAME = "vetbuddy.vault.envelope"
ENVELOPE_VERSION = "1"


def facts_canonical(facts: FactSet) -> List[dict]:
    """The facts as they entered the engine; session-only facts reduced to their key."""
    out = []
    for key in sorted(facts.keys()):
        fact = facts.facts[key]
        entry = {"key": key, "provenance": fact.provenance, "certain": fact.certain}
        if fact.key != "severe_disability":
            entry["value"] = fact.value
        out.append(entry)
    return out


def _texts(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if key not in ("official_url", "url", "rule", "benefit_id", "source_id", "lead_ids", "fact_key"):
                yield from _texts(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _texts(item)


def build(registry: VaultRegistry, *, kind: str, mode: str, policy: Optional[str], inputs: Mapping[str, Any],
          payload: Mapping[str, Any], language: LanguageGuard) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "envelope": ENVELOPE_NAME,
        "envelope_version": ENVELOPE_VERSION,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "registry": {"version": registry.version, "as_of": registry.as_of, "sha256": registry.sha256},
        "kind": kind,
        "mode": mode,
        "publish_policy": policy,
        "determination": "none",
        "notice": registry.notice,
        **payload,
    }
    found = language.check_all(_texts(body))
    if found:
        raise OutputBlocked(found)
    body["hashes"] = {
        "inputs": sha256_hex({"kind": kind, "mode": mode, "registry": registry.sha256,
                              "engine": ENGINE_VERSION, "inputs": inputs}),
        "output": sha256_hex(body),
    }
    return body
