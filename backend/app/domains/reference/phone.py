"""Phone normalization for dedupe and safety checks.

Ported from the Women Veterans module (wv_provenance.normalize_phone), which
fixed defect A-6: a naive digit-strip turned "988 (Press 1)" into "9881",
so the Veterans Crisis Line appeared twice. Trailing instruction text is
ignored rather than concatenated, and short codes (988, 838255, 88788) are
returned bare because they are not E.164.

The normalized value is a dedupe/safety KEY only. Never dedupe on phone
alone: VA's MST coordinator and the Women Veterans Call Center share a
number, and phone-only dedupe silently dropped the MST row (defect A-7).
"""
from __future__ import annotations

import re

_DIGITS = re.compile(r"\d+")


def normalize_phone(raw: str | None) -> str | None:
    if not raw:
        return None
    groups = _DIGITS.findall(raw)
    if not groups:
        return None
    acc = ""
    for g in groups:
        acc += g
        if len(acc) == 10:
            return "+1" + acc
        if len(acc) == 11 and acc.startswith("1"):
            return "+" + acc
        if len(acc) > 11:
            break
    first = groups[0]
    if 3 <= len(first) <= 6:
        return first  # short code
    if len(first) in (10, 11):
        return "+" + ("1" + first if len(first) == 10 else first)
    return None
