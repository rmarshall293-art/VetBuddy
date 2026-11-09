"""Canonical JSON and hashing shared by every vault module.

One canonical form is used everywhere a hash is taken: keys sorted,
separators (',', ':'), UTF-8, ``ensure_ascii`` false, and NaN or infinity
refused. It matches the coverage registry's integrity rule in migration 0013,
so the two registries hash the same way.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any

GENESIS_HASH = "0" * 64


def canonical_json(obj: Any) -> str:
    """Return the canonical JSON text of ``obj``."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=_default,
    )


def canonical_bytes(obj: Any) -> bytes:
    return canonical_json(obj).encode("utf-8")


def sha256_hex(data: Any) -> str:
    """SHA-256 of bytes, text, or the canonical JSON of any other object."""
    if isinstance(data, bytes):
        raw = data
    elif isinstance(data, str):
        raw = data.encode("utf-8")
    else:
        raw = canonical_bytes(data)
    return hashlib.sha256(raw).hexdigest()


def utc_iso(moment: datetime) -> str:
    """UTC timestamp text with microseconds and a Z suffix.

    PostgreSQL produces the same text with
    ``to_char(ts AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')``,
    which is how the pull ledger's hash chain is checked on both sides.
    """
    if moment.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_utc(text: str) -> datetime:
    """Parse an ISO 8601 timestamp that carries a timezone."""
    value = text.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        raise ValueError("timestamp must carry a timezone")
    return moment.astimezone(timezone.utc)


def _default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return utc_iso(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    raise TypeError(f"not JSON serializable: {type(obj).__name__}")
