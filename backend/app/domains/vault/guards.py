"""Pipeline guards for the Benefit Vault agent.

The vault runs the platform pipeline in this order:

    CrisisGate -> MSTNarrativeGuard -> PIIMinimizer -> engines (matcher, search)
    -> CitationValidator -> ClaimsBoundaryGuard -> (model call: none in this build)
    -> OutputGuard -> ApprovalGate (writes only) -> audit (pull ledger)

The language rules come from the single versioned file
``config/governance_language.yaml`` and the crisis contacts from
``config/crisis_floor.yaml``; nothing here restates them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import yaml

from .governance.egress import url_problem
from .vocab import OUTCOMES

CONFIG_DIR = Path(__file__).resolve().parents[4] / "config"
LANGUAGE_FILE = CONFIG_DIR / "governance_language.yaml"
CRISIS_FILE = CONFIG_DIR / "crisis_floor.yaml"
RETIRED_CRISIS_DIGITS = "18002738255"
REQUIRED_TEXT_KEYS = ("common_notice", "standard_disclaimer", "vso_referral_block")


def normalize(text: str) -> str:
    """Lower case, fold punctuation that separates words, collapse spaces.

    Matching is phrase-level on normalized text, never on exact substrings
    (the Education Navigator defect was exact matching that missed natural
    phrasing).
    """
    lowered = text.lower().replace("’", "'")
    folded = re.sub(r"[^\w$%.,'\s-]", " ", lowered)
    return re.sub(r"\s+", " ", folded).strip()


@dataclass(frozen=True)
class Violation:
    category: str
    pattern: str
    text: str


class LanguageGuard:
    """OutputGuard and ClaimsBoundaryGuard share this pattern set."""

    def __init__(self, path: Path = LANGUAGE_FILE):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.version = str(data["version"])
        self.patterns: List[Tuple[str, re.Pattern]] = []
        for category, entry in data["prohibited"].items():
            for pattern in entry["patterns"]:
                self.patterns.append((category, re.compile(pattern)))
        if not self.patterns:
            raise ValueError("governance language has no prohibited patterns")
        # Mandated wording (the v6 common notice and the standard disclaimer)
        # negates the prohibited phrases it names ("not ... a guarantee of
        # approval"). Only an exact, whitespace-folded copy of a required text
        # is exempt, so the exemption cannot carry any other wording.
        self.required = frozenset(" ".join(str(data[k]).split()) for k in REQUIRED_TEXT_KEYS if data.get(k))

    def violations(self, text: str) -> List[Violation]:
        if " ".join(text.split()) in self.required:
            return []
        normalized = normalize(text)
        return [Violation(cat, rx.pattern, text) for cat, rx in self.patterns if rx.search(normalized)]

    def check_all(self, texts: Iterable[str]) -> List[Violation]:
        found: List[Violation] = []
        for text in texts:
            if text:
                found.extend(self.violations(text))
        return found


class OutputBlocked(RuntimeError):
    def __init__(self, violations: Sequence[Violation]):
        super().__init__("; ".join(f"{v.category}: {v.pattern}" for v in violations))
        self.violations = list(violations)


@dataclass(frozen=True)
class CrisisContact:
    key: str
    label: str
    phone: Optional[str]
    extra: Optional[str]
    text: Optional[str]
    chat_url: Optional[str]


class CrisisGate:
    """Stops the pipeline and returns the crisis floor when a query signals crisis."""

    SIGNALS = (
        r"\bkill(ing)? myself\b", r"\bend(ing)? my life\b", r"\bsuicid(e|al)\b", r"\bwant to die\b",
        r"\bdon'?t want to (live|be here)\b", r"\bhurt(ing)? myself\b", r"\bself[- ]harm\b",
        r"\boverdos(e|ing)\b", r"\bno reason to live\b", r"\bbetter off dead\b",
    )

    def __init__(self, path: Path = CRISIS_FILE):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.contacts = tuple(
            CrisisContact(str(c["key"]), c["label"], c.get("phone"), c.get("extra"), c.get("text"), c.get("chat_url"))
            for c in data["contacts"]
        )
        self.emergency = data["emergency"]
        for contact in self.contacts:
            digits = re.sub(r"\D", "", f"{contact.phone or ''}{contact.text or ''}")
            if RETIRED_CRISIS_DIGITS in digits:
                raise ValueError("the crisis floor names the retired crisis number")
        self._signals = [re.compile(p) for p in self.SIGNALS]

    def triggered(self, text: Optional[str]) -> bool:
        if not text:
            return False
        normalized = normalize(text)
        return any(rx.search(normalized) for rx in self._signals)

    def response(self) -> dict:
        return {
            "crisis_floor": True,
            "message": "You don't have to go through this alone. Help is available right now.",
            "contacts": [
                {k: v for k, v in contact.__dict__.items() if v is not None} for contact in self.contacts
            ],
            "emergency": dict(self.emergency),
        }


class MSTNarrativeGuard:
    """The vault neither stores nor processes accounts of military sexual trauma.

    It answers with support resources from the crisis floor and stops. The
    benefits search can still be used with a plain query such as "MST support".
    """

    SIGNALS = (
        r"\b(i|we) (was|were|got|have been|had been) (sexually )?(assaulted|raped|abused)\b",
        r"\b(he|she|they|someone|somebody) (raped|sexually assaulted|assaulted|groped|molested) me\b",
        r"\bmy (rapist|attacker|abuser)\b",
    )

    def __init__(self, crisis: CrisisGate):
        self._signals = [re.compile(p) for p in self.SIGNALS]
        self._contacts = [c for c in crisis.contacts if c.key in ("dod_safe_helpline", "veterans_crisis_line")]

    def triggered(self, text: Optional[str]) -> bool:
        if not text:
            return False
        normalized = normalize(text)
        return any(rx.search(normalized) for rx in self._signals)

    def response(self) -> dict:
        return {
            "narrative_not_processed": True,
            "message": ("This search does not keep or read personal accounts. Confidential support is available, "
                        "and VA offers free MST-related care whatever your discharge or rating."),
            "contacts": [{k: v for k, v in c.__dict__.items() if v is not None} for c in self._contacts],
        }


class PIIMinimizer:
    """Remove identifiers from free text before any engine sees it."""

    PATTERNS = (
        ("ssn", re.compile(r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b")),
        ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
        ("phone", re.compile(r"(?<!\d)(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}(?!\d)")),
        ("dod_id", re.compile(r"\b\d{10}\b")),
        ("date", re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")),
    )

    def minimize(self, text: Optional[str]) -> Tuple[str, List[str]]:
        if not text:
            return "", []
        removed = []
        cleaned = text
        for kind, rx in self.PATTERNS:
            if rx.search(cleaned):
                removed.append(kind)
                cleaned = rx.sub(" ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()[:200]
        return cleaned, removed


class CitationValidator:
    """Every link shown must be plain https on the egress allowlist (the same test as fetching)."""

    def __init__(self, allowed_hosts: Iterable[str]):
        self.allowed = frozenset(h.lower() for h in allowed_hosts)

    def ok(self, url: Optional[str]) -> bool:
        return url_problem(url, self.allowed) is None


class ClaimsBoundaryGuard:
    """Every outcome stays inside the v6 set.

    Wording is checked once, over the whole response, by the OutputGuard in
    the envelope (``LanguageGuard``), so no text can claim a determination.
    """

    def check(self, items: Sequence[dict]) -> List[Violation]:
        found: List[Violation] = []
        for item in items:
            if item.get("outcome") not in OUTCOMES:
                found.append(Violation("outcome", "v6 outcome set", str(item.get("outcome"))))
        return found


class ApprovalRequired(PermissionError):
    """A write was attempted without the person's explicit confirmation."""

    def __init__(self, action: str, consent_text: str):
        super().__init__(f"{action} needs the person's confirmation")
        self.action = action
        self.consent_text = consent_text


class ApprovalGate:
    """Writes (a grant, a saved benefit) happen only after the person confirms."""

    def require(self, action: str, confirmed: bool, consent_text: str) -> None:
        if confirmed is not True:
            raise ApprovalRequired(action, consent_text)
