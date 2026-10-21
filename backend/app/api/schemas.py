"""Request contracts for /api/v1. Unknown fields are rejected (422).

`extra="forbid"` is how R14 holds at the edge: a request carrying an SSN, a
diagnosis, or any field the router does not need is refused before it is
read, rather than silently dropped or stored.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..kernel.router import RouterInput


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RouterRequest(Strict):
    persona: str = Field(max_length=40)
    branch: str = Field(max_length=40)
    component: str = Field(max_length=40)
    current_jurisdiction: str = Field(max_length=12)
    destination_jurisdiction: str | None = Field(default=None, max_length=12)
    legal_authority: str | None = Field(default=None, max_length=40)
    separation_date: date | None = None
    goals: list[str] = Field(default_factory=list, max_length=8)
    urgency: str = Field(default="30_days", max_length=20)

    def to_input(self) -> RouterInput:
        return RouterInput(
            persona=self.persona, branch=self.branch, component=self.component,
            current_jurisdiction=self.current_jurisdiction, destination_jurisdiction=self.destination_jurisdiction,
            legal_authority=self.legal_authority, separation_date=self.separation_date,
            goals=tuple(self.goals), urgency=self.urgency,
        )


class RatingsRequest(Strict):
    ratings: list[int] = Field(default_factory=list, max_length=40)
    bilateral: list[int] = Field(default_factory=list, max_length=20)


class ConsentRequest(Strict):
    purpose: str = Field(max_length=60)


class TaskUpdate(Strict):
    status: Literal["todo", "in_progress", "done", "cancelled"]
    expected_version: int = Field(ge=1)


class DevTokenRequest(Strict):
    subject: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_.@:-]+$")
    tenant: str = Field(default="public", max_length=63)
