"""
The ONE authored crisis-floor definition for the whole platform.

Fixes the pinned defect where four front ends each carried their own copy,
with disagreeing minimum sizes (<3 in one service, !=5 in another). Every
surface — API, web shell, standalone app (via a generated copy), career
module, WV module — reads THIS file's data, never a hand-written copy.

Slice 02 merged the Women Veterans module floor into the same config, so the
required set grew from three contacts to six.
"""
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).parents[3] / "config" / "crisis_floor.yaml"

REQUIRED_KEYS = frozenset({
    "veterans_crisis_line", "988", "domestic_violence_hotline",
    "women_veterans_call_center", "homeless_veterans_call_center", "dod_safe_helpline",
})


def _config() -> dict:
    return yaml.safe_load(_CONFIG_PATH.read_text())


def load_crisis_contacts() -> list[dict]:
    return _config()["contacts"]


def retired_numbers() -> dict[str, str]:
    """E.164 numbers that must never appear anywhere as a live contact."""
    return dict(_config().get("retired_numbers") or {})


def crisis_floor_satisfied() -> bool:
    """Mirrors CrisisGate.floor_satisfied from the real prototype: the
    service must not report ready until every required contact is present
    and correctly formatted (see the pinned '988 normalized to 9881'
    defect — contacts must survive redaction verbatim)."""
    contacts = load_crisis_contacts()
    present = {c["key"] for c in contacts}
    if not REQUIRED_KEYS.issubset(present):
        return False
    vcl = next(c for c in contacts if c["key"] == "veterans_crisis_line")
    return vcl.get("phone") == "988" and vcl.get("extra") == "Press 1"
