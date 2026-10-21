"""Reference data loader: data/reference/*.json is the single author of
governance wording, rule status, the legal lane, sources, transition windows
and contested readings. The API serves it read-only; scripts/build_web.py
generates the browser's copy from it.

Loading validates the corpus and refuses to start on a broken one: every
cited source must exist, every status must be in the vocabulary, and no row
may claim VERIFIED without a named reviewer and date (G1).
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "data" / "reference"
DATASETS = ("governance", "sources", "transition_timeline", "conflicts")

ROW_STATUSES = {"UNVERIFIED", "SOURCE_CHECKED", "CONTESTED", "SUPERSEDED", "VERIFIED", "ILLUSTRATIVE", "HEURISTIC",
                "RESOLVED_BY_DESIGN"}
REPO_STATUSES = {"IMPLEMENTED_VERIFIED", "IMPLEMENTED_UNTESTED", "PARTIAL", "MOCK", "NOT_PRESENT", "BLOCKED_SOURCE",
                 "DEFERRED"}
LANE_ALLOWED = {"yes", "share_card", "no"}


class ReferenceDataError(ValueError):
    pass


def _dir() -> Path:
    return Path(os.environ.get("VB_REFERENCE_DIR") or DEFAULT_DIR)


@lru_cache(maxsize=1)
def load() -> dict[str, dict]:
    data = {name: json.loads((_dir() / f"{name}.json").read_text()) for name in DATASETS}
    validate(data)
    return data


def validate(data: dict[str, dict]) -> None:
    def fail(msg: str):
        raise ReferenceDataError(msg)

    sources = data["sources"]["sources"]
    for sid, s in sources.items():
        if not sid.startswith("src.") or not s.get("title") or not s.get("origin"):
            fail(f"source {sid} needs an id, title and origin")
        if s.get("tier") not in (None, 1, 2, 3, 4):
            fail(f"source {sid} has unknown tier {s.get('tier')}")

    tl = data["transition_timeline"]
    if tl["default_status"] not in ROW_STATUSES:
        fail("timeline default_status not in vocabulary")
    ids = set()
    for w in tl["windows"]:
        if w["id"] in ids:
            fail(f"duplicate window {w['id']}")
        ids.add(w["id"])
        if not w["sources"] or any(s not in sources for s in w["sources"]):
            fail(f"window {w['id']} cites an unknown or empty source list")
        status = w.get("status", tl["default_status"])
        if status not in ROW_STATUSES:
            fail(f"window {w['id']} status {status} not in vocabulary")
        if status == "VERIFIED" and not (w.get("verified_by") and w.get("verified_on")):
            fail(f"window {w['id']} is VERIFIED without a named reviewer and date")

    gov = data["governance"]
    for s in gov["_meta"]["sources"] + data["conflicts"]["_meta"]["sources"]:
        if s not in sources:
            fail(f"governance cites unknown source {s}")
    for group in ("agent_rules", "tier0_rules", "release_gates"):
        for r in gov[group]:
            if r["repo_status"] not in REPO_STATUSES:
                fail(f"{group} {r['id']} has status {r['repo_status']}")
    if [r["id"] for r in gov["agent_rules"]] != [f"R{i}" for i in range(1, 23)]:
        fail("agent_rules must be exactly R1..R22 in order")
    for row in gov["legal_lane"]:
        if row["allowed"] not in LANE_ALLOWED:
            fail(f"legal lane value {row['allowed']}")
    for c in data["conflicts"]["conflicts"]:
        if c["status"] not in ROW_STATUSES or len(c["readings"]) < 2 and c["status"] == "CONTESTED":
            fail(f"conflict {c['subject']} needs a status and two or more readings")


def governance() -> dict:
    return load()["governance"]
