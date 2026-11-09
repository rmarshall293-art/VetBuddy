"""Source watcher: notice when a source page changes or is due for review.

``due`` lists sources read longer ago than the review period; the matcher
already reports their records as SOURCE_STALE. ``check`` re-reads pages with
an injected fetcher and compares a hash of the normalized text with the last
baseline, so a changed page sends its records to the review queue.

No fetcher is wired in this build (the hosting decision is open), so ``check``
without one reports every source as BLOCKED rather than pretending to watch.
The research read pages through a summarizing tool, so no raw-page baselines
exist yet; the first real run records them (status NEW_BASELINE).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from ..canonical import sha256_hex
from ..governance.egress import EgressBlocked, EgressGuard

WATCH_STATUSES = ("UNCHANGED", "CHANGED", "NEW_BASELINE", "UNREACHABLE", "BLOCKED")


def normalize_page(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


@dataclass(frozen=True)
class WatchFinding:
    source_id: str
    url: Optional[str]
    status: str
    content_sha256: Optional[str]
    affected_benefit_ids: Tuple[str, ...]
    note: str

    def view(self) -> dict:
        return {**self.__dict__, "affected_benefit_ids": list(self.affected_benefit_ids)}


class SourceWatcher:
    def __init__(self, registry, egress: EgressGuard, fetch: Optional[Callable[[str], str]] = None,
                 baselines: Optional[Mapping[str, str]] = None):
        self.registry = registry
        self.egress = egress
        self.fetch = fetch
        self.baselines: Dict[str, str] = dict(baselines or {})
        self._affected: Dict[str, List[str]] = {}
        for benefit in registry.benefits.values():
            self._affected.setdefault(benefit.source_id, []).append(benefit.benefit_id)

    def due(self, as_of: date) -> List[dict]:
        limit = int(self.registry.governance["review"]["stale_after_days"])
        out = []
        for source_id, source in sorted(self.registry.sources.items()):
            stamp = source.get("opened_on") or source.get("seen_on")
            age = (as_of - date.fromisoformat(stamp)).days if stamp else None
            if age is None or age > limit:
                out.append({"source_id": source_id, "url": source["url"], "last_read": stamp, "age_days": age,
                            "records": len(self._affected.get(source_id, ()))})
        return out

    def check(self, source_ids: Optional[Iterable[str]] = None) -> List[WatchFinding]:
        wanted = sorted(source_ids) if source_ids is not None else sorted(self.registry.sources)
        findings = []
        for source_id in wanted:
            source = self.registry.sources[source_id]
            url = source["url"]
            affected = tuple(sorted(self._affected.get(source_id, ())))
            if url is None:
                findings.append(WatchFinding(source_id, None, "BLOCKED", None, affected, "seen in search only; no page to watch"))
                continue
            if self.fetch is None:
                findings.append(WatchFinding(source_id, url, "BLOCKED", None, affected, "no fetcher is wired"))
                continue
            try:
                self.egress.check_url(url)
            except EgressBlocked as exc:
                findings.append(WatchFinding(source_id, url, "BLOCKED", None, affected, exc.reason))
                continue
            try:
                text = self.fetch(url)
            except Exception as exc:  # a dead page is a finding, not a crash
                findings.append(WatchFinding(source_id, url, "UNREACHABLE", None, affected, type(exc).__name__))
                continue
            digest = sha256_hex(normalize_page(text))
            previous = self.baselines.get(source_id)
            if previous is None:
                status, note = "NEW_BASELINE", "first baseline recorded"
            elif previous == digest:
                status, note = "UNCHANGED", "same as the last baseline"
            else:
                status, note = "CHANGED", "page changed; its records need review"
            self.baselines[source_id] = digest
            findings.append(WatchFinding(source_id, url, status, digest, affected if status == "CHANGED" else (), note))
        return findings
