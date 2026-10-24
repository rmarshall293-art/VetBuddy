"""Settings from environment variables. Names only in git; values never.

DATABASE_URL       migration/owner connection (used only by `python -m app.migrate`)
APP_DATABASE_URL   the API's least-privilege login (member of vetbuddy_app)
AUTH_MODE          "off" (default: every private route answers 401) or "dev"
AUTH_DEV_SECRET    HMAC key for development tokens; required when AUTH_MODE=dev
ENVIRONMENT        development | test | staging | production
CORS_ORIGINS       comma-separated browser origins allowed to call the API
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    environment: str
    app_database_url: str | None
    auth_mode: str
    auth_dev_secret: str | None
    cors_origins: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "Settings":
        s = cls(
            environment=os.environ.get("ENVIRONMENT", "development"),
            app_database_url=os.environ.get("APP_DATABASE_URL") or None,
            auth_mode=os.environ.get("AUTH_MODE", "off"),
            auth_dev_secret=os.environ.get("AUTH_DEV_SECRET") or None,
            cors_origins=tuple(o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()),
        )
        s.check()
        return s

    def check(self) -> None:
        if self.auth_mode not in ("off", "dev"):
            raise ConfigError("AUTH_MODE must be 'off' or 'dev' (a real identity provider is not wired yet: G17)")
        if self.auth_mode == "dev" and self.environment in ("staging", "production"):
            raise ConfigError("development sign-in cannot run in staging or production")
        if self.auth_mode == "dev" and (not self.auth_dev_secret or len(self.auth_dev_secret) < 32):
            raise ConfigError("AUTH_DEV_SECRET must be at least 32 characters when AUTH_MODE=dev")
