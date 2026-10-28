"""Consent is checked inside the same transaction as every protected read or
write — not cached, not checked once at login. Revocation therefore takes
effect on the very next request (master spec §20 #5, #11)."""
from __future__ import annotations

import uuid

from app.infra.db import Connection

MISSION_PURPOSE = "personal_mission_planning"


class ConsentRequired(Exception):
    def __init__(self, purpose: str):
        super().__init__(purpose)
        self.purpose = purpose


def active_consent(conn: Connection, user_id: uuid.UUID, purpose: str) -> dict | None:
    return conn.one(
        "SELECT consent_id, purpose, data_categories, granted_at FROM consent_record"
        " WHERE user_id = $1 AND purpose = $2 AND revoked_at IS NULL ORDER BY granted_at DESC LIMIT 1",
        [user_id, purpose])


def require(conn: Connection, user_id: uuid.UUID, purpose: str = MISSION_PURPOSE) -> dict:
    c = active_consent(conn, user_id, purpose)
    if c is None:
        raise ConsentRequired(purpose)
    return c
