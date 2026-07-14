"""Application configuration via environment variables.

Never hardcode secrets. Copy `.env.example` to `.env` for local development.
Live VA Lighthouse and Stripe production keys must be supplied at deploy time.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "VetBuddy"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Security / JWT
    secret_key: str = "CHANGE_ME_DEV_ONLY_use_openssl_rand_hex_32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # Database
    database_url: str = "postgresql+psycopg2://vetbuddy:vetbuddy@localhost:5432/vetbuddy"

    # Redis (optional — app runs without Redis using in-memory fallbacks)
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Stripe (test mode by default — never commit live keys)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_consumer: str = ""
    stripe_publishable_key: str = ""
    stripe_mock_mode: bool = True
    consumer_price_cents: int = 599

    # VA Lighthouse / FHIR (sandbox — register at developer.va.gov)
    va_client_id: str = ""
    va_client_secret: str = ""
    va_redirect_uri: str = "http://localhost:8000/api/v1/va/lighthouse/callback"
    va_api_base_url: str = "https://sandbox-api.va.gov"
    va_mock_mode: bool = True

    # OAuth placeholders (Google / Apple — wire when credentials available)
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    apple_oauth_client_id: str = ""
    apple_oauth_team_id: str = ""

    # Rate limiting placeholder
    rate_limit_per_minute: int = 120

    # Logging / error tracking hooks
    log_level: str = "INFO"
    sentry_dsn: str = ""  # Optional Sentry DSN for production error tracking

    # Frontend URL (Stripe redirects, emails)
    frontend_url: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
