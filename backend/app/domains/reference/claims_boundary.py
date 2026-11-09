"""ClaimsBoundaryGuard pattern scan (Agent Governance Rules §3, T0-01..03; §7).

Deterministic and pure. Patterns come from config/governance_language.yaml,
the single versioned source legal review edits. Matching is phrase-level on
normalized text, not exact substrings (the Education Navigator defect).

This is the scan only. Its runtime placement — before the model call and
again inside OutputGuard — arrives with the agent runtime (R16/R11 era).
Today it gates the reference corpus and task copy in tests.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_PATH = Path(__file__).parents[4] / "config" / "governance_language.yaml"


@dataclass(frozen=True)
class Hit:
    category: str
    pattern: str
    excerpt: str
    allowed_alternative: str


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‘", "'")
    text = re.sub(r"[\"“”()\[\]{}:;,!?]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=1)
def language() -> dict:
    return yaml.safe_load(_PATH.read_text())


@lru_cache(maxsize=1)
def _compiled() -> tuple[tuple[str, re.Pattern, str], ...]:
    out = []
    for category, spec in language()["prohibited"].items():
        for p in spec["patterns"]:
            out.append((category, re.compile(p), spec["allowed_alternative"]))
    return tuple(out)


def scan(text: str) -> list[Hit]:
    norm = normalize(text)
    hits = []
    for category, pat, alt in _compiled():
        m = pat.search(norm)
        if m:
            lo, hi = max(0, m.start() - 30), min(len(norm), m.end() + 30)
            hits.append(Hit(category, pat.pattern, norm[lo:hi], alt))
    return hits


def required_text(key: str) -> str:
    """Disclaimers and blocks, whitespace-folded (no route restates them)."""
    return " ".join(str(language()[key]).split())
