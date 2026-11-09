"""Named-reviewer verification for Benefit Vault records (gate G1; V21; migration 0016).

The project owner keeps the roster in ``config/reviewer_roster.yaml`` (handles
only). ``sync_roster`` copies it into ``ref.vault_reviewer``; a reviewer who
leaves the file is retired, never deleted, so past reviews stay attributable.

A review is one owner-run transaction: the record's current content hash must
equal the hash the reviewer read (the queue prints it), the database refuses a
handle that is not active on the roster or not scoped to the record's
jurisdiction, and the action is written to the append-only review log. The API
applies VERIFIED marks at startup (``load_reviews``), and the seed keeps a mark
only while the reviewed content is unchanged.

Everything here takes an owner connection from ``app.infra.db``; the app role
can read neither the roster nor the log.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import List, Optional

import yaml

from .vocab import REVIEWER_HANDLE

ROOT = Path(__file__).resolve().parents[4]
ROSTER_FILE = ROOT / "config" / "reviewer_roster.yaml"
ROLES = ("accredited_vso_representative", "accredited_claims_agent", "accredited_attorney", "state_veterans_agency")
# The owner's decision: Alabama first, then records whose source was already checked.
QUEUE_ORDER = ("CASE WHEN jurisdiction = 'AL' THEN 0 ELSE 1 END, "
               "CASE WHEN record_status = 'SOURCE_CHECKED' THEN 0 ELSE 1 END, jurisdiction, category, benefit_id")


class ReviewError(ValueError):
    pass


def load_roster(path: Path = ROSTER_FILE) -> List[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if data.get("owner") != "project_owner":
        raise ReviewError("the roster's owner must be project_owner")
    reviewers = data.get("reviewers") or []
    seen = set()
    for r in reviewers:
        handle = str(r.get("handle", ""))
        if not re.fullmatch(REVIEWER_HANDLE, handle):
            raise ReviewError(f"{handle!r} is not a handle (lowercase letters, digits, . _ -; never a name or email)")
        if handle in seen:
            raise ReviewError(f"{handle} is listed twice")
        seen.add(handle)
        if r.get("role") not in ROLES:
            raise ReviewError(f"{handle}: role must be one of {', '.join(ROLES)}")
        scope = r.get("scope") or []
        if not scope or not all(s == "*" or re.fullmatch(r"[A-Z]{2}", str(s)) for s in scope):
            raise ReviewError(f"{handle}: scope is a list of jurisdiction codes or '*'")
        if not isinstance(r.get("added_on"), dt.date):
            raise ReviewError(f"{handle}: added_on must be a date (YYYY-MM-DD)")
        unknown = set(r) - {"handle", "role", "scope", "added_on", "active"}
        if unknown:
            raise ReviewError(f"{handle}: unexpected fields {sorted(unknown)} (handles only; no names or contacts)")
    return reviewers


def sync_roster(conn, reviewers: List[dict], today: dt.date) -> dict:
    """Upsert the roster; anyone missing from the file is retired, never deleted."""
    listed = []
    with conn.transaction():
        for r in reviewers:
            active = r.get("active", True) is not False
            conn.query(
                "INSERT INTO ref.vault_reviewer (handle, role, scope, added_on, added_by, active, retired_on)"
                " VALUES ($1, $2, $3, $4, 'project_owner', $5, $6)"
                " ON CONFLICT (handle) DO UPDATE SET role = EXCLUDED.role, scope = EXCLUDED.scope,"
                " added_on = EXCLUDED.added_on, active = EXCLUDED.active,"
                " retired_on = CASE WHEN EXCLUDED.active THEN NULL"
                "                   ELSE COALESCE(ref.vault_reviewer.retired_on, EXCLUDED.retired_on) END",
                [r["handle"], r["role"], list(r["scope"]), r["added_on"], active, None if active else today])
            listed.append(r["handle"])
        retired = conn.query(
            "UPDATE ref.vault_reviewer SET active = false, retired_on = COALESCE(retired_on, $1)"
            " WHERE active AND NOT (handle = ANY($2)) RETURNING handle", [today, listed])
    return {"active": sorted(r["handle"] for r in reviewers if r.get("active", True) is not False),
            "retired": sorted(r["handle"] for r in retired)}


def queue(conn, limit: int = 25, jurisdiction: Optional[str] = None) -> List[dict]:
    """Records awaiting review, in the owner's order. Links seen only in search can't be verified."""
    where = "record_status IN ('UNVERIFIED', 'SOURCE_CHECKED') AND official_url_status <> 'SEEN_IN_SEARCH'"
    params: list = [limit]
    if jurisdiction:
        where += " AND jurisdiction = $2"
        params.append(jurisdiction)
    return conn.query(f"SELECT benefit_id, jurisdiction, category, record_status, title, official_url, content_hash"
                      f" FROM ref.vault_benefit WHERE {where} ORDER BY {QUEUE_ORDER} LIMIT $1", params)


def verify(conn, benefit_id: str, handle: str, content_hash: str, on: dt.date) -> dict:
    with conn.transaction():
        row = conn.one("SELECT content_hash, record_status, official_url_status FROM ref.vault_benefit"
                       " WHERE benefit_id = $1 FOR UPDATE", [benefit_id])
        if row is None:
            raise ReviewError(f"no record {benefit_id}")
        if row["content_hash"] != content_hash:
            raise ReviewError("the record changed since it was read: review the current version (see the queue)")
        if row["record_status"] == "VERIFIED":
            raise ReviewError(f"{benefit_id} is already verified")
        if row["official_url_status"] == "SEEN_IN_SEARCH":
            raise ReviewError("a link seen only in search can't be verified; open the official page first")
        conn.query("UPDATE ref.vault_benefit SET record_status = 'VERIFIED', verified_by = $2, verified_on = $3,"
                   " verified_content_hash = content_hash WHERE benefit_id = $1", [benefit_id, handle, on])
        conn.query("INSERT INTO ref.vault_review_event (benefit_id, action, handle, content_hash, on_date)"
                   " VALUES ($1, 'VERIFIED', $2, $3, $4)", [benefit_id, handle, content_hash, on])
    return {"benefit_id": benefit_id, "verified_by": handle, "verified_on": on.isoformat()}


def withdraw(conn, benefit_id: str, registry_status: str, on: dt.date) -> dict:
    """Undo a review: the record returns to its registry status; the log keeps both events."""
    if registry_status == "VERIFIED":
        raise ReviewError("the registry never ships a VERIFIED record")
    with conn.transaction():
        row = conn.one("SELECT verified_by, content_hash FROM ref.vault_benefit WHERE benefit_id = $1"
                       " AND record_status = 'VERIFIED' FOR UPDATE", [benefit_id])
        if row is None:
            raise ReviewError(f"{benefit_id} is not verified")
        conn.query("UPDATE ref.vault_benefit SET record_status = $2, verified_by = NULL, verified_on = NULL,"
                   " verified_content_hash = NULL WHERE benefit_id = $1", [benefit_id, registry_status])
        conn.query("INSERT INTO ref.vault_review_event (benefit_id, action, handle, content_hash, on_date)"
                   " VALUES ($1, 'WITHDRAWN', $2, $3, $4)", [benefit_id, row["verified_by"], row["content_hash"], on])
    return {"benefit_id": benefit_id, "record_status": registry_status}
