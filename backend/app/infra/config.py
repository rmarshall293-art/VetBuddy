"""Environment contract. Variable NAMES only live in code and .env.example;
values come from the environment / secret store, never from git."""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    database_url: str          # non-owner app role (vb_app). Never the schema owner.
    auth_mode: str             # "dev" (MOCK signed tokens) | "disabled"
    dev_token_secret: bytes
    mode_c_enabled: bool       # privacy Mode C (managed case) — off until reviewed
    web_dir: Path


def load() -> Settings:
    secret = os.environ.get("VB_DEV_TOKEN_SECRET")
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "host=localhost port=5432 user=vb_app dbname=vetbuddy_dev"),
        auth_mode=os.environ.get("VB_AUTH_MODE", "disabled"),
        # Random per process if unset: dev tokens die with the process.
        dev_token_secret=secret.encode() if secret else secrets.token_bytes(32),
        mode_c_enabled=os.environ.get("VB_MODE_C_ENABLED", "false").lower() == "true",
        web_dir=ROOT / "web",
    )
