"""Required language and the ClaimsBoundaryGuard pattern list (governance §7).

These strings live here, versioned, not in prompts, so the guard can check for
them and legal review can change them in one place. Wording of the required
blocks is copied from VetBuddy Agent Governance Rules (20 Oct 2026) and still
needs attorney / accredited-agent review before public launch (§12).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

LANGUAGE_VERSION = "governance-language.v1.0.0"

AI_DISCLOSURE = (
    "VetBuddy is software. It is not VA, a Veterans Service Organization, an attorney or a clinician. "
    "It explains and organizes; it does not decide claims, file anything, or guarantee an outcome."
)

STANDARD_DISCLAIMER = (
    "VetBuddy provides information and recommendations only. It does not guarantee any benefit, rating, "
    "or outcome, and it is not a substitute for an accredited representative. VA alone decides eligibility "
    "and disability ratings."
)

VSO_REFERRAL = (
    "For help preparing or filing a VA claim, work with a VA-accredited Veterans Service Organization "
    "representative, claims agent, or attorney. Accredited VSO help is free. You can find one using VA's "
    "accredited representative search, or through a VSO such as The American Legion, DAV, or VFW."
)

CFR_REFERENCE_LABEL = (
    "This is VA's published regulation, shown for reference. It explains how VA describes criteria; "
    "it is not an assessment of your condition."
)

RESUME_LABEL = "Draft built from the information you provided. Review every line before you use it."

FIND_REP_URL = "https://www.va.gov/get-help-from-accredited-representative/find-rep/"


@dataclass(frozen=True)
class Violation:
    category: str
    pattern: str
    excerpt: str


# Phrase-level patterns over normalized text (lowercase, straight quotes,
# collapsed whitespace) — exact substrings missed natural phrasing before.
PROHIBITED: dict[str, tuple[str, ...]] = {
    "guarantee": (
        r"\byou(?:'ll| will) (?:definitely )?(?:get|receive)\b(?! help)",
        r"\byou (?:do |definitely )?qualify for\b",
        r"\bguaranteed?\b(?! (?:any|a|an) )",
        r"\byou(?:'re| are) owed\b",
        r"\byou(?:'re| are) (?:eligible|entitled)\b",
    ),
    "rating": (
        r"\byou (?:should|will|would) be rated\b",
        r"\b(?:is|are) worth \d{1,3} ?%",
        r"\blikely \d{1,3} ?%",
        r"\byour (?:likely|expected|probable) rating\b",
    ),
    "diagnosis": (
        r"\byou (?:have|probably have|likely have) (?:ptsd|tbi|sleep apnea|tinnitus|depression|anxiety)\b",
        r"\bsounds like (?:ptsd|tbi|sleep apnea|tinnitus|depression|anxiety)\b",
    ),
    "representation": (
        r"\bwe(?:'ll| will)? file\b",
        r"\bwe represent you\b",
        r"\byour claim agent\b",
        r"\bvetbuddy (?:will|can) (?:file|submit|sign)\b",
    ),
    "claim_coaching": (
        r"\btell the examiner\b",
        r"\bdescribe it as\b",
        r"\bdon't mention\b",
    ),
    "fees": (
        r"\$\d[\d,]*(?:\.\d\d)? (?:to|for) (?:file|appeal|increase)",
        r"\bfee (?:for|to) (?:file|filing|appeal)",
    ),
}

_COMPILED = {cat: tuple(re.compile(p) for p in pats) for cat, pats in PROHIBITED.items()}


def normalize(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


def check_text(text: str) -> list[Violation]:
    """ClaimsBoundaryGuard: return every prohibited phrase found. Empty = pass."""
    norm = normalize(text)
    found = []
    for cat, pats in _COMPILED.items():
        for p in pats:
            m = p.search(norm)
            if m:
                found.append(Violation(cat, p.pattern, norm[max(0, m.start() - 30): m.end() + 30]))
    return found
