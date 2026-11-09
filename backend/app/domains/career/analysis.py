"""Announcement extraction, matching, qualification matrix and competitiveness.

Fixes carried from the specification (ADR 0007 maps each to a test):
  D-2  whole-token matching on a stemmed haystack that includes the record title
       ("art" no longer matches "quartermaster"; "supervising" meets "supervised")
  D-3  generic qualifiers ("current", "valid", ...) are stopwords, not keywords
  D-4  a record of absence (negative) is never support; it is reported as an absence
  D-5  a legally required credential blocks unless verified support is MODERATE or better
  D-6  non-qualification headings are tested first ("REQUIRED DOCUMENTS" is not a requirement)
  D-7  wrapped prose lines are joined before extraction
  D-8  one tokenizer for keywords and haystack (hyphens and possessives match)
  D-9  short tokens (acronyms) are never stemmed (BLS, ACLS, WMS)
  D1   an all-MODERATE category with no gaps is "Competitive with minor gaps"
New in this rebuild (found by running the sample people):
  CN-11 an empty evidence bank yields "Insufficient information", never a gap:
        not knowing is not a negative finding
  CN-12 a legally required credential the person holds but hasn't verified gets
        "verify it", not "go get it"
  CN-13 a legally required credential is supported only by a credential record
        (a dispatch job mentioning "drivers" is not a CDL), and a record of
        absence speaks only to credential, clearance and education
        requirements (a "clearance not recorded" note is not an experience gap)
  CB-01 protected and health content is removed from the haystack before
        matching, so it can neither help nor hurt a match
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

from .enforcement import RULES, EvidenceBank, EvidenceItem, redact_protected

STOPWORDS = frozenset(RULES["stopwords"])
CATEGORY_RULES: Tuple[Tuple[str, bool, "re.Pattern[str]"], ...] = tuple(
    (cat, legal, re.compile(p, re.I)) for cat, legal, p in RULES["req_category_rules"])
HEAD_OTHER = re.compile(RULES["headings"]["other"])
HEAD_PREF = re.compile(RULES["headings"]["preferred"])
HEAD_REQ = re.compile(RULES["headings"]["required"])
BULLET = re.compile(r"^[-•*]\s+")
HEADING = re.compile(r"^[A-Z][A-Z\s,'&/-]{6,}$")
STATUS_LABELS: Tuple[str, ...] = tuple(RULES["status_labels"])
MAX_KEYWORDS = 10


# ── tokenizer (one, shared: D-8) ─────────────────────────────────────────────

def stem(word: str) -> str:
    word = re.sub(r"'s$", "", word)
    if len(word) <= 4:                       # D-9: acronyms and short words are atoms
        return word
    word = re.sub(r"(?:ations?|ions?|ing|ed|es|s)$", "", word)
    return re.sub(r"(?:iz|is)$", "", word)


def tokens(text: str) -> List[str]:
    return [t for t in (stem(w) for w in re.split(r"[^a-z0-9+']+", text.lower()) if w.strip("'")) if len(t) > 2]


def haystack(text: str) -> str:
    """Leading and trailing spaces make ' kw ' a whole-token test, first and last tokens included."""
    return " " + " ".join(tokens(redact_protected(text))) + " "


def keywords_from(text: str) -> List[str]:
    out: List[str] = []
    for t in tokens(text):
        if t in STOPWORDS or t.strip("+").isdigit() or t in out:
            continue
        out.append(t)
    return out[:MAX_KEYWORDS]


# ── extraction ───────────────────────────────────────────────────────────────

class ReqKind(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"


@dataclass(frozen=True)
class JobRequirement:
    requirement_id: str
    text: str
    kind: ReqKind
    category: str
    keywords: Tuple[str, ...]
    legally_required: bool = False


def join_wrapped(raw: str) -> List[str]:
    """D-7: a line continues its predecessor unless either is a bullet or heading
    or the predecessor ends a sentence; blank lines break paragraphs."""
    out: List[str] = []
    for line in (l.strip() for l in raw.splitlines()):
        prev = out[-1] if out else ""
        prev_open = (bool(prev) and not BULLET.match(prev) and not HEADING.match(prev)
                     and not re.search(r"[.:;]$", prev))
        if line and not BULLET.match(line) and not HEADING.match(line) and prev_open:
            out[-1] = prev + " " + line
        else:
            out.append(line)
    return out


def categorize(text: str) -> Tuple[str, bool]:
    for cat, legal, pat in CATEGORY_RULES:   # order is load-bearing: legal licence rules first
        if pat.search(text):
            return cat, legal
    return "other", False


def extract_requirements(raw: str) -> List[JobRequirement]:
    mode: Optional[ReqKind] = None
    reqs: List[JobRequirement] = []
    for line in join_wrapped(raw):
        if HEAD_OTHER.match(line):           # D-6: tested first
            mode = None
            continue
        if HEAD_PREF.match(line):
            mode = ReqKind.PREFERRED
            continue
        if HEAD_REQ.match(line):
            mode = ReqKind.REQUIRED
            continue
        if mode is None:
            continue
        prose = (mode is ReqKind.REQUIRED and len(line) > 28 and re.match(r"^[A-Z]", line)
                 and not re.fullmatch(r"[A-Z\s,]+", line))
        if not (BULLET.match(line) or prose):
            continue
        text = re.sub(r"\.$", "", BULLET.sub("", line)).strip()
        if len(text) < 8:
            continue
        cat, legal = categorize(text)
        reqs.append(JobRequirement(f"r{len(reqs) + 1}", text, mode, cat, tuple(keywords_from(text)), legal))
    return reqs


# ── matrix ───────────────────────────────────────────────────────────────────

class Strength(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"


SUPPORTED = (Strength.STRONG, Strength.MODERATE)
LEGAL_ROUTE = ("Required by law; experience can't substitute for it. Route to the Education Navigator for the "
               "credential, and don't apply until it is in place.")
LEGAL_VERIFY = ("Required by law. You have a record of it that isn't verified yet: upload or attest it. "
                "Until then it can't count, and applying now isn't reasonable.")
CLEARANCE_ACTION = ("Record the clearance's level and current status if you hold one. Employers sponsor clearances; "
                    "VetBuddy doesn't assess eligibility for one.")
ABSENCE_SPEAKS_TO = frozenset({"credential", "clearance", "education"})


@dataclass(frozen=True)
class MatrixRow:
    requirement: JobRequirement
    evidence_ids: Tuple[str, ...]          # top 3 verified, never unverified
    unverified_ids: Tuple[str, ...]
    absence_ids: Tuple[str, ...]
    strength: Strength
    gap: Optional[str]
    action: str
    blocking: bool
    needs_confirmation: bool


def _score(item: EvidenceItem, req: JobRequirement) -> int:
    hay = haystack("\n".join([item.title, item.summary, *item.skills]))   # field boundaries are clause boundaries
    return sum(1 for kw in req.keywords if f" {kw} " in hay)


def build_matrix(requirements: Sequence[JobRequirement], bank: EvidenceBank) -> List[MatrixRow]:
    rows = []
    items = bank.all()
    for req in requirements:
        hits, absences = [], []
        for item in items:
            if req.legally_required and item.kind != "credential":        # CN-13
                continue
            s = _score(item, req)
            if not s:
                continue
            if item.negative:
                if req.category in ABSENCE_SPEAKS_TO:                    # CN-13
                    absences.append((s, item))
                continue
            hits.append((s, item))
        hits.sort(key=lambda h: (-h[0], h[1].evidence_id))
        verified = [(s, i) for s, i in hits if i.outbound]
        unverified = [(s, i) for s, i in hits if not i.outbound]
        if not hits:
            strength = Strength.NONE
        elif not verified:
            strength = Strength.WEAK
        elif verified[0][0] >= 2 and len(verified) >= 2:
            strength = Strength.STRONG
        elif verified[0][0] >= 2 or len(verified) > 1:
            strength = Strength.MODERATE
        else:
            strength = Strength.WEAK

        gap: Optional[str] = None
        if strength is Strength.NONE:
            gap = f"No evidence found for: {req.text}"
            if req.legally_required:
                action = LEGAL_ROUTE
            elif req.category == "clearance":
                action = CLEARANCE_ACTION
            elif req.kind is ReqKind.REQUIRED:
                action = "Route to the Education Navigator, or record the experience if you have it."
            else:
                action = "Applying without it is reasonable."
        elif strength is Strength.WEAK:
            gap = "Evidence exists but is thin or unverified."
            action = "Verify the supporting record, then add one measurable accomplishment."
        elif strength is Strength.MODERATE:
            action = "Add one measurable accomplishment."
        else:
            action = "No action needed."
        blocking = req.legally_required and strength not in SUPPORTED          # D-5
        needs_confirmation = bool(unverified) and not verified
        if blocking:
            gap = gap or "Not established by verified evidence."
            action = LEGAL_VERIFY if needs_confirmation else LEGAL_ROUTE      # CN-12
        if absences:                                                          # D-4
            gap = (gap + " " if gap else "") + "A record on file documents its absence."
            if req.legally_required:
                action = LEGAL_ROUTE
            elif req.category == "clearance":
                action = CLEARANCE_ACTION
            else:
                action = "A record on file says this isn't in place. Resolve it, or route to the Education Navigator."
        rows.append(MatrixRow(req, tuple(i.evidence_id for _, i in verified[:3]),
                              tuple(i.evidence_id for _, i in unverified), tuple(i.evidence_id for _, i in absences),
                              strength, gap, action, blocking, needs_confirmation))
    return rows


def relevance(item: EvidenceItem, requirements: Sequence[JobRequirement]) -> int:
    """Tailoring weight for ordering a resume: required hits count 2, preferred 1."""
    return sum(_score(item, r) * (2 if r.kind is ReqKind.REQUIRED else 1) for r in requirements)


# ── competitiveness ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CategoryScore:
    category: str
    label: str
    basis: str
    source: str


def label_for(strengths: Sequence[Strength], blocking: bool, bank_empty: bool = False) -> str:
    if not strengths or bank_empty:
        return "Insufficient information"                                     # CN-11
    if blocking:
        return "Significant qualifications gap"
    n = len(strengths)
    strong = sum(s is Strength.STRONG for s in strengths)
    weak = sum(s is Strength.WEAK for s in strengths)
    none_ = sum(s is Strength.NONE for s in strengths)
    if none_ == 0 and strong / n >= 0.60:
        return "Strong match"
    if none_ <= 1 and strong / n >= 0.30:
        return "Competitive with minor gaps"
    if none_ == 0 and weak == 0:                                              # D1
        return "Competitive with minor gaps"
    if none_ <= max(1, n // 3):
        return "Potential match with addressable gaps"
    return "Significant qualifications gap"


def competitiveness(rows: Sequence[MatrixRow], bank: EvidenceBank) -> List[CategoryScore]:
    """One label per category, never a composite number: a single score invites
    reading it as a hiring probability."""
    by_cat: Dict[str, List[MatrixRow]] = {}
    for r in rows:
        by_cat.setdefault(r.requirement.category, []).append(r)
    out = []
    for cat, rs in sorted(by_cat.items()):
        covered = sum(r.strength in SUPPORTED for r in rs)
        out.append(CategoryScore(cat, label_for([r.strength for r in rs], any(r.blocking for r in rs), len(bank) == 0),
                                 f"{covered} of {len(rs)} requirements supported by verified evidence",
                                 "Announcement text as provided; your evidence bank"))
    return out
