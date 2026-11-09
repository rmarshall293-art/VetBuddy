"""Import the research ledgers into benefit records.

The ledgers under ``data/research`` are pipe-separated text written while the
pages were read (format in ``data/research/RESEARCH_LOG.md``). This module is
the only reader. It turns each row into a benefit record with:

* a stable id (jurisdiction plus a slug of the title),
* the rule in canonical spelling, checked against the rule language,
* the page that was actually read (the source) and its tier,
* how the vault knows the official link: the same page, a link taken from the
  page, or a link only seen in search results,
* a record status: SOURCE_CHECKED when the page read was the program's own page
  (tier 1 or 3), UNVERIFIED otherwise. Nothing is ever imported as VERIFIED;
  that needs a named reviewer (gate G1).

RULE may contain ``|`` (the OR operator), so each row is split by taking three
fields from the left and three from the right; the middle is the rule.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlsplit

from ..canonical import sha256_hex
from ..rules import RuleError, compile_rule, tokens
from ..vocab import CATEGORIES, GROUPS, JURISDICTIONS, STATE_CATEGORIES

HEADER = re.compile(r"^#\s*JUR=(?P<jur>[A-Z]{2})\s+SRC=(?P<src>\S+)(?P<rest>.*)$")
ATTR = re.compile(r"([A-Z_]+)=(\S+)")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
FETCHED = re.compile(r"(?:fetched|read)\s+(\d{4}-\d{2}-\d{2})")

TITLE_MAX, WHO_MAX, VALUE_MAX = 140, 280, 240

# Host lists that decide tier and kind. Kept here, beside the only reader,
# and copied into the registry so a reviewer sees the same list the code uses.
TIER2_HOSTS = frozenset({
    "myarmybenefits.us.army.mil", "www.myairforcebenefits.us.af.mil", "myairforcebenefits.us.af.mil",
    "law.justia.com", "regulations.justia.com", "news.va.gov",
})
COMMERCIAL_HOSTS = frozenset({
    "corporate.homedepot.com", "www.lowes.com", "www.amtrak.com", "www.t-mobile.com", "www.verizon.com",
    "www.hilton.com", "www.sixflags.com", "wavesofhonor.com", "www.shadesofgreen.org",
})
NONPROFIT_HOSTS = frozenset({
    "www.fisherhouse.org", "www.taps.org", "foldsofhonor.org", "www.legion.org", "www.vfw.org",
    "www.mcsf.org", "www.nmcrs.org", "afas.org", "mycgma.org", "pattillmanfoundation.org",
    "www.vettix.org", "scholarships.militaryfamily.org",
})
# Department of Defense resorts and clubs run as MWR programs. Their own pages
# are the operator's page (tier 3) but the program is federal MWR, not a deal.
MWR_OPERATOR_HOSTS = frozenset({"www.halekoa.com", "www.afvclub.com"})
# Shades of Green sells Disney's military tickets; its eligibility page is MWR,
# its ticket page is Disney's commercial offer.
SHADES_ELIGIBILITY = "https://www.shadesofgreen.org/about-shades-green/eligibility"


class LedgerError(ValueError):
    """A ledger row or header that cannot be imported."""

    def __init__(self, path: str, line: int, message: str):
        super().__init__(f"{path}:{line}: {message}")
        self.path, self.line = path, line


@dataclass
class Block:
    path: str
    line: int
    jurisdiction: str
    src: Optional[str]
    attrs: Dict[str, str]

    @property
    def part(self) -> str:
        return self.attrs.get("PART", "main")


@dataclass
class Row:
    block: Block
    line: int
    category: str
    title: str
    groups: Tuple[str, ...]
    rule: str
    who: str
    value: str
    url: str


@dataclass
class Ledger:
    path: str
    opened_on: Optional[str]
    blocks: List[Block] = field(default_factory=list)
    rows: List[Row] = field(default_factory=list)


def host_of(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def tier_for(url: Optional[str]) -> int:
    """Tier of a page by its host (see vocab.TIERS)."""
    if not url:
        return 4
    host = host_of(url)
    if host in TIER2_HOSTS:
        return 2
    if host.endswith((".gov", ".mil")) or re.search(r"\.(gov|mil)\.[a-z]{2}$", host) or host.endswith(".us"):
        return 1
    return 3


def split_row(text: str) -> Tuple[str, str, str, str, str, str, str]:
    parts = text.split("|")
    if len(parts) < 7:
        raise ValueError(f"a row needs 7 fields, found {len(parts)}")
    left, right = parts[:3], parts[-3:]
    rule = "|".join(parts[3:-3])
    return left[0], left[1], left[2], rule, right[0], right[1], right[2]


def parse_ledger(path: Path, base: Path) -> Ledger:
    rel = path.relative_to(base).as_posix()
    text = path.read_text(encoding="utf-8")
    fetched = FETCHED.search(text)
    ledger = Ledger(rel, fetched.group(1) if fetched else None)
    block: Optional[Block] = None
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("#"):
            header = HEADER.match(line)
            if header:
                jur = header.group("jur")
                if jur not in JURISDICTIONS:
                    raise LedgerError(rel, number, f"unknown jurisdiction {jur}")
                src = header.group("src")
                attrs = dict(ATTR.findall(header.group("rest")))
                if src == "none":
                    if "SEEN_IN_SEARCH" not in attrs:
                        raise LedgerError(rel, number, "a block without a source page must say SEEN_IN_SEARCH=<date>")
                    src = None
                elif not src.startswith("https://"):
                    raise LedgerError(rel, number, "SRC must be an https URL or none")
                for key in ("PAGE_UPDATED", "OPENED", "SEEN_IN_SEARCH"):
                    if key in attrs and attrs[key] != "none" and not DATE.fullmatch(attrs[key]):
                        raise LedgerError(rel, number, f"{key} must be a date or none")
                if "TAIL_UNREAD" in attrs and not attrs["TAIL_UNREAD"].isdigit():
                    raise LedgerError(rel, number, "TAIL_UNREAD must be a character count")
                block = Block(rel, number, jur, src, attrs)
                ledger.blocks.append(block)
            continue
        if block is None:
            raise LedgerError(rel, number, "row before any JUR header")
        try:
            category, title, groups, rule, who, value, url = (field_.strip() for field_ in split_row(line))
        except ValueError as exc:
            raise LedgerError(rel, number, str(exc)) from None
        ledger.rows.append(Row(block, number, category, title, tuple(g.strip() for g in groups.split(",")),
                               rule, who, value, url))
    return ledger


def slug(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    folded = re.sub(r"[^a-z0-9]+", "-", folded).strip("-")
    return folded[:72].rstrip("-")


def source_id(url: Optional[str], seen_date: Optional[str]) -> str:
    if url is None:
        return f"src.search.{seen_date}"
    return "src." + sha256_hex(url)[:16]


def _kind(row: Row, official_url: str) -> str:
    if row.block.jurisdiction != "US":
        return "STATE_BENEFIT"
    host = host_of(row.block.src or official_url)
    if host in COMMERCIAL_HOSTS and (row.block.src or "") != SHADES_ELIGIBILITY:
        return "COMMERCIAL_DEAL"
    if host in NONPROFIT_HOSTS:
        return "NONPROFIT_PROGRAM"
    return "FEDERAL_BENEFIT"


def _check_text(row: Row, name: str, value: str, limit: int) -> None:
    if not value:
        raise LedgerError(row.block.path, row.line, f"{name} is empty")
    if len(value) > limit:
        raise LedgerError(row.block.path, row.line, f"{name} is longer than {limit} characters")
    if any(ord(ch) < 32 for ch in value):
        raise LedgerError(row.block.path, row.line, f"{name} has a control character")


def build(ledgers: Iterable[Ledger], default_opened_on: str):
    """Return (sources, benefits, tail_reads) built from parsed ledgers."""
    sources: Dict[str, dict] = {}
    benefits: List[dict] = []
    ids: Dict[str, int] = {}
    tail_reads: List[dict] = []
    for ledger in ledgers:
        opened_default = ledger.opened_on or default_opened_on
        for block in ledger.blocks:
            seen_date = block.attrs.get("SEEN_IN_SEARCH")
            sid = source_id(block.src, seen_date)
            page_updated = block.attrs.get("PAGE_UPDATED")
            entry = sources.get(sid)
            if entry is None:
                entry = {
                    "source_id": sid,
                    "url": block.src,
                    "page_status": "OPENED" if block.src else "SEEN_IN_SEARCH",
                    "tier": tier_for(block.src),
                    "opened_on": (block.attrs.get("OPENED") or opened_default) if block.src else None,
                    "seen_on": seen_date,
                    "page_updated": None if page_updated in (None, "none") else page_updated,
                    "tail_unread_chars": 0,
                    "parts_read": [],
                    "ledgers": [],
                }
                sources[sid] = entry
            if block.part not in entry["parts_read"]:
                entry["parts_read"].append(block.part)
            if ledger.path not in entry["ledgers"]:
                entry["ledgers"].append(ledger.path)
            if block.part == "main" and "TAIL_UNREAD" in block.attrs:
                entry["tail_unread_chars"] = int(block.attrs["TAIL_UNREAD"])
            if block.part == "tail":
                tail_reads.append({"jurisdiction": block.jurisdiction, "source_id": sid, "ledger": ledger.path,
                                   "line": block.line})
        for row in ledger.rows:
            benefits.append(_record(row, sources, ids))
    for entry in sources.values():
        entry["parts_read"].sort()
        entry["ledgers"].sort()
    return sorted(sources.values(), key=lambda s: s["source_id"]), benefits, tail_reads


def _record(row: Row, sources: Dict[str, dict], ids: Dict[str, int]) -> dict:
    block = row.block
    where = (block.path, row.line)
    if row.category not in CATEGORIES:
        raise LedgerError(*where, f"unknown category {row.category}")
    if block.jurisdiction != "US" and row.category not in STATE_CATEGORIES:
        raise LedgerError(*where, f"{row.category} is a federal-only category")
    for group in row.groups:
        if group not in GROUPS:
            raise LedgerError(*where, f"unknown group {group!r}")
    if len(set(row.groups)) != len(row.groups):
        raise LedgerError(*where, "a group is listed twice")
    _check_text(row, "TITLE", row.title, TITLE_MAX)
    _check_text(row, "ELIGIBLE", row.who, WHO_MAX)
    _check_text(row, "VALUE", row.value, VALUE_MAX)
    try:
        node, canonical = compile_rule(row.rule)
    except RuleError as exc:
        raise LedgerError(*where, str(exc)) from None
    if row.url == "PAGE":
        if block.src is None:
            raise LedgerError(*where, "PAGE needs a source page")
        official_url, url_status = block.src, "SAME_AS_SOURCE"
    elif row.url.startswith("https://") and " " not in row.url:
        official_url = row.url
        if block.src is None:
            url_status = "SEEN_IN_SEARCH"
        else:
            url_status = "SAME_AS_SOURCE" if row.url == block.src else "LINKED_FROM_SOURCE"
    else:
        raise LedgerError(*where, "URL must be an https link or PAGE")
    sid = source_id(block.src, block.attrs.get("SEEN_IN_SEARCH"))
    source = sources[sid]
    tier = source["tier"]
    record_status = "SOURCE_CHECKED" if source["page_status"] == "OPENED" and tier in (1, 3) else "UNVERIFIED"
    base = f"{block.jurisdiction.lower()}.{slug(row.title)}"
    count = ids.get(base, 0) + 1
    ids[base] = count
    benefit_id = base if count == 1 else f"{base}-{count}"
    content = {
        "jurisdiction": block.jurisdiction,
        "category": row.category,
        "title": row.title,
        "groups": list(row.groups),
        "rule": canonical,
        "who_it_is_for": row.who,
        "value": row.value,
        "official_url": official_url,
    }
    return {
        "benefit_id": benefit_id,
        **content,
        "rule_tokens": sorted({t.render() for t in tokens(node)}),
        "kind": _kind(row, official_url),
        "source_id": sid,
        "source_tier": tier,
        "official_url_status": url_status,
        "official_url_tier": tier_for(official_url),
        "record_status": record_status,
        "page_part": block.part,
        "ledger_ref": f"{block.path}:{row.line}",
        "content_hash": sha256_hex(content),
    }


def load_all(research_dir: Path, default_opened_on: str):
    paths = sorted(research_dir.glob("states/*.psv")) + sorted(research_dir.glob("federal/*.psv"))
    ledgers = [parse_ledger(path, research_dir) for path in paths]
    return ledgers, build(ledgers, default_opened_on)
