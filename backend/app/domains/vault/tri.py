"""Three-valued (strong Kleene) logic.

A missing fact is UNKNOWN, and UNKNOWN propagates. It never silently becomes
FALSE, and FALSE is never presented as "ineligible": the matcher turns it
into DOES_NOT_MEET_ENCODED_RULES, which says only that the encoded
conditions are not met.

Order: FALSE < UNKNOWN < TRUE. AND is the minimum, OR the maximum, and NOT
maps UNKNOWN to UNKNOWN. The truth tables are pinned by tests so this module
can be swapped for the bridge's ``tri`` module at integration only if the two
agree exactly.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable


class Tri(Enum):
    FALSE = 0
    UNKNOWN = 1
    TRUE = 2

    @staticmethod
    def of(value: bool) -> "Tri":
        if not isinstance(value, bool):
            raise TypeError("Tri.of takes a bool")
        return Tri.TRUE if value else Tri.FALSE

    def __and__(self, other: "Tri") -> "Tri":
        return Tri(min(self.value, other.value))

    def __or__(self, other: "Tri") -> "Tri":
        return Tri(max(self.value, other.value))

    def __invert__(self) -> "Tri":
        if self is Tri.UNKNOWN:
            return Tri.UNKNOWN
        return Tri.FALSE if self is Tri.TRUE else Tri.TRUE

    def __bool__(self) -> bool:  # pragma: no cover - guard against misuse
        raise TypeError("a Tri has no plain truth value; compare it with Tri.TRUE")


def all_of(values: Iterable[Tri]) -> Tri:
    result = Tri.TRUE
    for value in values:
        result = result & value
    return result


def any_of(values: Iterable[Tri]) -> Tri:
    result = Tri.FALSE
    for value in values:
        result = result | value
    return result
