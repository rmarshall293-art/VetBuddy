"""Load the synthetic career samples (data/demo/career.json) into evidence banks.

Used by the demo build and the tests; never by a route. Every record is invented."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .enforcement import AuditLog, EvidenceBank, EvidenceItem, Metric, Verification

SAMPLES_FILE = Path(__file__).resolve().parents[4] / "data" / "demo" / "career.json"


def load_samples(path: Path = SAMPLES_FILE) -> Dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8"))["people"]


def item_from(record: dict) -> EvidenceItem:
    r = dict(record)
    r["verification"] = Verification(r.get("verification", "unverified"))
    r["metrics"] = tuple(Metric(**{**m, "verification": Verification(m.get("verification", "unverified"))})
                         for m in r.get("metrics", ()))
    r["skills"] = tuple(r.get("skills", ()))
    return EvidenceItem(**r)


def bank_for(person: dict, audit: AuditLog) -> EvidenceBank:
    return EvidenceBank(audit, (item_from(r) for r in person["evidence"]))
