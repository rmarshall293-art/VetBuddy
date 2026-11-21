"""Recovered Guard & Reserve research leads (ADR 0011 addendum).

The owner-supplied Gemini report is an AI-written secondary source (tier 4).
Its extraction is loaded only when every file matches its hash in
RECOVERY_MANIFEST.json, and is shown only as leads:

- record_status UNVERIFIED, tier 4, with the source the report names (not
  opened by VetBuddy) and the ``recovered_ai_lead`` caveat;
- never an outcome, never a record, never a match input;
- a cell the governance language guard flags is withheld, not reworded, and
  the person is pointed to the named source instead.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

from .policy import ROOT, GuardReservePolicy, PolicyError

RECOVERED_DIR = ROOT / "data" / "research" / "recovered"
COLUMNS = ("education", "income_tax", "property_tax", "other")


def _read(rel: str, entries: Dict[str, dict], recovered_dir: Path) -> dict:
    entry = entries.get(rel)
    if entry is None:
        raise PolicyError(f"{rel} is not in RECOVERY_MANIFEST.json")
    data = (recovered_dir / rel).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise PolicyError(f"{rel} does not match its recovery manifest hash")
    return json.loads(data.decode("utf-8"))


class RecoveredLeads:
    def __init__(self, policy: GuardReservePolicy, recovered_dir: Path = RECOVERED_DIR):
        spec = policy.raw["recovered"]
        manifest = json.loads((recovered_dir / "RECOVERY_MANIFEST.json").read_text(encoding="utf-8"))
        entries = {e["path"]: e for e in manifest["entries"]}
        self.entries = {k: entries[k] for k in (spec["jurisdictions"], spec["federal"]) if k in entries}
        self.notice = " ".join(spec["notice"].split())
        self.caveat = {"id": "recovered_ai_lead", "text": policy.caveats["recovered_ai_lead"]}
        jur = _read(spec["jurisdictions"], entries, recovered_dir)
        fed = _read(spec["federal"], entries, recovered_dir)
        self.provenance = {"recovered_from": entries[spec["jurisdictions"]]["recovered_from"], "tier": 4,
                           "record_status": "UNVERIFIED",
                           "datasets": [{"path": k, "sha256": v["sha256"]} for k, v in self.entries.items()]}
        self.jurisdictions: Dict[str, dict] = {r["code"]: r for r in jur["jurisdictions"]}
        self.report_consistency: List[dict] = jur["report_consistency"]
        self.cross_check_counts: Dict[str, int] = jur["cross_check_counts"]
        self.relations: Dict[str, str] = jur["relations"]
        self.federal: List[dict] = fed["leads"]
        gaps = {g["id"] for g in policy.research_gaps}
        for lead in self.federal:
            if not set(lead["statuses"]) <= set(policy.statuses):
                raise PolicyError(f"{lead['lead_id']} names an unknown duty status")
            if not set(lead["gap_ids"]) <= gaps:
                raise PolicyError(f"{lead['lead_id']} names an unknown research gap")
        self.priority: List[str] = list(spec["source_check_priority"])
        if sorted(self.priority) != sorted(l["lead_id"] for l in self.federal):
            raise PolicyError("source_check_priority must name every federal lead exactly once")
        if len(self.jurisdictions) != 56:
            raise PolicyError("the recovered jurisdiction table must have 56 rows")

    def jurisdiction(self, code: str) -> Optional[dict]:
        row = self.jurisdictions.get(code)
        if row is None:
            return None
        flags = row["language_flags"]
        cells = {col: (None if col in flags else row[col]) for col in COLUMNS}
        return {"lead_id": f"GJ.{code}", "kind": "recovered_lead", "code": code, "name": row["name"],
                **cells, "withheld_by_language_guard": sorted(flags),
                "named_source": row["named_source"], "source_opened": False, "tags": row["tags"],
                "vault_cross_check": {**row["cross_check"], "meaning": self.relations[row["cross_check"]["relation"]]},
                "record_status": "UNVERIFIED", "tier": 4, "caveats": [self.caveat]}

    def federal_for(self, duty_status: Optional[str]) -> List[dict]:
        leads = [lead for lead in self.federal if duty_status is None or duty_status in lead["statuses"]]
        return [{"lead_id": lead["lead_id"], "kind": "recovered_lead", "topic": lead["topic"], "claim": lead["claim"],
                 "citation": lead["citation"], "named_sources": lead["named_sources"], "source_opened": False,
                 "review_note": lead.get("review_note"), "gap_ids": lead["gap_ids"],
                 "record_status": "UNVERIFIED", "tier": 4, "caveats": [self.caveat]} for lead in leads]

    def for_person(self, duty_status: Optional[str], codes: List[str]) -> dict:
        rows = [self.jurisdiction(c) for c in dict.fromkeys(c for c in codes if c)]
        return {"notice": self.notice, "provenance": self.provenance,
                "jurisdictions": [r for r in rows if r], "federal": self.federal_for(duty_status)}

    def summary(self) -> dict:
        return {"notice": self.notice, "provenance": self.provenance, "report_consistency": self.report_consistency,
                "vault_cross_check_counts": self.cross_check_counts, "relations": self.relations,
                "federal_leads": len(self.federal), "jurisdiction_rows": len(self.jurisdictions)}

    def source_queue(self, egress) -> List[dict]:
        """Every source the report names, in the order to open them. Nothing here has been opened.

        Each URL appears once, with every lead that cites it. ``host_known`` is the
        egress guard's answer: true when the host is already on the vault's allowlist
        (a page there has been read before). A new host joins the allowlist only when a
        ledger row from a page read on it is imported.
        """
        order: List[str] = []
        cites: Dict[str, List[str]] = {}
        gaps: Dict[str, List[str]] = {}
        by_id = {l["lead_id"]: l for l in self.federal}
        for lead_id in self.priority:
            for url in by_id[lead_id]["named_sources"]:
                if url not in cites:
                    order.append(url)
                cites.setdefault(url, []).append(lead_id)
                gaps.setdefault(url, [])
                gaps[url] = sorted(set(gaps[url]) | set(by_id[lead_id]["gap_ids"]))
        rows = sorted(self.jurisdictions.values(), key=lambda r: ("agr_specific_rule" not in r["tags"], r["code"]))
        for row in rows:
            url = row["named_source"]
            if url not in cites:
                order.append(url)
            cites.setdefault(url, []).append(f"GJ.{row['code']}")
            gaps.setdefault(url, [])
        return [{"rank": i + 1, "url": url, "cited_by": cites[url], "gap_ids": gaps[url],
                 "host_known": egress.allowed(url), "state": "NOT_OPENED"} for i, url in enumerate(order)]
