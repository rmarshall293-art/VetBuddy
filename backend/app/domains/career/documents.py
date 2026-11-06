"""Document proposals: resume (six types), cover letter and STAR stories.

Generators propose; DocumentAssembler disposes. A generator may over-propose
(and the demo build deliberately proposes one invented figure so the gate can
be seen working); nothing reaches a document except through the gate.

Rules kept from the specification (§16.6) and gaps closed (§16.3):
  - generators read only outbound evidence: never unverified records, never
    records of absence, and sensitive records only with a per-document opt-in
  - every employer-facing line, role headers and the skills line included,
    goes through the gate, so protected content in a title is caught too
  - the cover letter goes through the same gate (the original checked it in
    the renderer); its opening and closing use the gate's no-provenance
    exemption, which refuses any number
  - a required qualification the person lacks is disclosed, never concealed
  - a STAR story missing its result is never completed by the system
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from .analysis import SUPPORTED, JobRequirement, MatrixRow, ReqKind, Strength, relevance
from .enforcement import (RULES, NEEDS_VERIFICATION, AssemblyResult, AuditLog, DocumentAssembler, EvidenceBank,
                          EvidenceItem, OUTBOUND_OK, Statement)

JARGON = tuple((re.compile(p, re.I), r) for p, r in RULES["jargon"])
MONTHS = ("", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December")
NAIVE_IMPACT = "Improved readiness by 23% and reduced downtime by 15%."


@dataclass(frozen=True)
class ResumeType:
    key: str
    label: str
    de_jargon: bool
    bullets: int
    hours: bool          # federal and state formats show hours per week
    summary: bool


RESUME_TYPES: Dict[str, ResumeType] = {t.key: t for t in (
    ResumeType("ats", "Private sector (ATS)", True, 4, False, True),
    ResumeType("federal", "Federal (USAJOBS)", True, 6, True, True),
    ResumeType("state", "State government", True, 5, True, True),
    ResumeType("jobfair", "Job fair one-page", True, 2, False, True),
    ResumeType("founder", "Founder / contractor", True, 3, False, True),
    ResumeType("master", "Master record (internal, keeps military terms)", False, 9, True, False),
)}


@dataclass(frozen=True)
class Person:
    name: str
    objective: str


@dataclass(frozen=True)
class Section:
    heading: str
    lines: Tuple[Statement, ...]


@dataclass(frozen=True)
class Document:
    kind: str
    title: str
    sections: Tuple[Section, ...]
    result: AssemblyResult


def de_jargon(text: str) -> str:
    for pat, rep in JARGON:
        text = pat.sub(rep, text)
    return text


def fmt_date(value: Optional[str]) -> str:
    if not value:
        return "Present"
    year, month = value.split("-")[:2]
    return f"{MONTHS[int(month)]} {year}"


def sentence_case(text: str) -> str:
    """Lower only an ordinary leading capital, so "GS-09", "STIGs" and "Security+" keep their case."""
    return text[0].lower() + text[1:] if len(text) > 1 and text[0].isupper() and text[1].islower() else text


def usable(item: EvidenceItem, opt_in: FrozenSet[str]) -> bool:
    return item.outbound and (not item.sensitive or item.evidence_id in opt_in)


def bullets_for(item: EvidenceItem, plain: bool) -> List[Statement]:
    clean = de_jargon if plain else (lambda s: s)
    out = [Statement(clean(s.strip()), (item.evidence_id,)) for s in re.split(r"(?<=\.)\s+", item.summary)
           if len(s.strip()) > 12]
    for m in item.metrics:
        if m.verification in OUTBOUND_OK:
            text = m.phrase.replace("{v}", m.value_text) if m.phrase else f"Accountable for {m.value_text} {m.meaning}."
            out.append(Statement(clean(text), (item.evidence_id,)))
    return out


def _assemble(bank: EvidenceBank, audit: AuditLog, sections: List[Tuple[str, List[Statement]]], *, kind: str,
              title: str, document_id: str, actor: str, opt_in: FrozenSet[str]) -> Document:
    flat = [s for _, lines in sections for s in lines]
    result = DocumentAssembler(bank, audit).assemble(flat, document_id=document_id, actor=actor,
                                                     sensitive_opt_in=opt_in)
    return Document(kind, title, tuple(Section(h, tuple(lines)) for h, lines in sections if lines), result)


def generate_resume(resume_type: str, person: Person, requirements: Sequence[JobRequirement], bank: EvidenceBank,
                    audit: AuditLog, *, actor: str, sensitive_opt_in: FrozenSet[str] = frozenset(),
                    demonstrate_gate: bool = False) -> Document:
    cfg = RESUME_TYPES[resume_type]
    items = [i for i in bank.all() if usable(i, sensitive_opt_in)]
    experience = [i for i in items if i.kind in ("military_experience", "civilian_experience")]
    experience.sort(key=lambda i: i.start_date or "", reverse=True)
    clean = de_jargon if cfg.de_jargon else (lambda s: s)
    sections: List[Tuple[str, List[Statement]]] = []
    if cfg.summary and experience:
        top = experience[:2]
        roles = " and ".join(clean(i.title.split(",")[0]) for i in top)
        sections.append(("Summary", [Statement(f"{person.objective.rstrip('.')}. Experience as {roles}.",
                                               tuple(i.evidence_id for i in top), "summary")]))
    # Tailoring: the record most relevant to this announcement leads, whatever its date.
    experience.sort(key=lambda i: (-relevance(i, requirements), -(int((i.start_date or "0").replace("-", "")))))
    lines: List[Statement] = []
    for item in experience:
        header = f"{clean(item.title)}" + (f", {item.org}" if item.org else "") + \
                 f", {fmt_date(item.start_date)} to {fmt_date(item.end_date)}"
        if cfg.hours and item.hours_per_week:
            header += f", {item.hours_per_week} hours per week"
        lines.append(Statement(header, (item.evidence_id,), "role"))
        proposals = bullets_for(item, cfg.de_jargon)[:cfg.bullets]
        if demonstrate_gate and resume_type == "ats" and item.kind == "military_experience":
            proposals.append(Statement(NAIVE_IMPACT, (item.evidence_id,)))   # appended after the cut: always reaches the gate
        lines.extend(proposals)
    sections.append(("Experience", lines))
    sections.append(("Education", [Statement(clean(i.title), (i.evidence_id,), "education")
                                   for i in items if i.kind == "education"]))
    sections.append(("Credentials", [Statement(clean(i.title), (i.evidence_id,), "credential")
                                     for i in items if i.kind == "credential"]))
    skills = list(dict.fromkeys(s for i in items for s in i.skills))
    if skills:
        sections.append(("Skills", [Statement("Skills: " + ", ".join(clean(s) for s in skills) + ".",
                                              tuple(i.evidence_id for i in items if i.skills), "skills")]))
    return _assemble(bank, audit, sections, kind=f"resume:{resume_type}", title=f"{cfg.label} resume",
                     document_id=f"resume_{resume_type}", actor=actor, opt_in=sensitive_opt_in)


def generate_cover_letter(position: str, employer: str, rows: Sequence[MatrixRow], bank: EvidenceBank,
                          audit: AuditLog, *, actor: str, sensitive_opt_in: FrozenSet[str] = frozenset()) -> Document:
    opening = Statement(f"I am applying for the {position} position with {employer}.", (), "opening",
                        no_provenance_ok=True)
    body: List[Statement] = []
    for r in [r for r in rows if r.strength in SUPPORTED][:3]:
        item = bank.get(r.evidence_ids[0])
        if item is None or not usable(item, sensitive_opt_in):
            continue
        first = re.split(r"(?<=\.)\s+", item.summary)[0].strip()
        req_text = sentence_case(r.requirement.text)
        body.append(Statement(f"You asked for {req_text}. {de_jargon(first)}", (item.evidence_id,), "evidence",
                              quoted=req_text))
    # Disclose a required qualification only when it is KNOWN to be missing: a legally
    # required credential that a record on file documents as absent. A requirement
    # with no evidence yet is unknown, not missing (CN-14): the matrix asks the person
    # to record it instead, and the letter makes no claim either way.
    gaps = [r for r in rows if r.requirement.kind is ReqKind.REQUIRED and r.blocking and r.absence_ids]
    disclosure = [Statement(f"I do not currently meet one posted requirement: {sentence_case(r.requirement.text)}. "
                            "I am addressing it and can discuss the timeline.", (), "gap_disclosure",
                            quoted=sentence_case(r.requirement.text), no_provenance_ok=True) for r in gaps[:1]]
    closing = Statement("Thank you for considering my application.", (), "closing", no_provenance_ok=True)
    return _assemble(bank, audit, [("Letter", [opening, *body, *disclosure, closing])], kind="cover_letter",
                     title="Cover letter", document_id="cover_letter", actor=actor, opt_in=sensitive_opt_in)


@dataclass(frozen=True)
class StarStory:
    evidence_id: str
    title: str
    situation: str
    action: Optional[str]
    result: Optional[str]          # None means "not recorded": rendered as NEEDS_VERIFICATION, never invented

    @property
    def complete(self) -> bool:
        return bool(self.situation and self.action and self.result)


def generate_star(bank: EvidenceBank) -> List[StarStory]:
    out = []
    for item in bank.all():
        if not item.outbound or item.sensitive or not (item.kind == "accomplishment" or item.metrics):
            continue
        parts = dict(re.findall(r"(Situation|Action|Result):\s*(.+?)(?=(?:Situation|Action|Result):|$)", item.summary,
                                flags=re.I | re.S))
        parts = {k.lower(): v.strip() for k, v in parts.items()}
        if parts:
            out.append(StarStory(item.evidence_id, item.title, parts.get("situation", ""), parts.get("action"),
                                 parts.get("result")))
        else:
            sentences = [s.strip() for s in re.split(r"(?<=\.)\s+", item.summary) if s.strip()]
            out.append(StarStory(item.evidence_id, item.title, sentences[0] if sentences else "",
                                 sentences[1] if len(sentences) > 1 else None, None))
    return out


__all__ = ["RESUME_TYPES", "Person", "Document", "Section", "StarStory", "generate_resume", "generate_cover_letter",
           "generate_star", "de_jargon", "fmt_date", "NEEDS_VERIFICATION"]
