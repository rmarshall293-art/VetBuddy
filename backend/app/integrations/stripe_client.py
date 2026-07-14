"""Stripe client wrapper — mock when keys absent."""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_checkout_session(
    *,
    customer_email: str,
    customer_id: Optional[str],
    success_url: str,
    cancel_url: str,
    price_cents: int,
) -> dict[str, Any]:
    settings = get_settings()
    if settings.stripe_mock_mode or not settings.stripe_secret_key:
        session_id = f"cs_test_mock_{uuid4().hex[:16]}"
        return {
            "session_id": session_id,
            "checkout_url": f"{success_url}&session_id={session_id}&mock=1",
            "mock": True,
        }

    # Live Stripe path — requires STRIPE_SECRET_KEY and STRIPE_PRICE_ID_CONSUMER
    import stripe

    stripe.api_key = settings.stripe_secret_key
    params: dict[str, Any] = {
        "mode": "subscription",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "line_items": [
            {
                "price": settings.stripe_price_id_consumer
                or None,
                "quantity": 1,
            }
        ],
        "customer_email": customer_email if not customer_id else None,
        "customer": customer_id,
    }
    # If no price ID configured, fall back to price_data for $5.99
    if not settings.stripe_price_id_consumer:
        params["line_items"] = [
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": price_cents,
                    "recurring": {"interval": "month"},
                    "product_data": {"name": "VetBuddy Consumer"},
                },
                "quantity": 1,
            }
        ]
    params = {k: v for k, v in params.items() if v is not None}
    session = stripe.checkout.Session.create(**params)
    return {
        "session_id": session.id,
        "checkout_url": session.url,
        "mock": False,
    }


def verify_webhook(payload: bytes, signature: Optional[str]) -> dict[str, Any]:
    settings = get_settings()
    if settings.stripe_mock_mode or not settings.stripe_webhook_secret:
        import json

        try:
            body = json.loads(payload.decode("utf-8") or "{}")
        except Exception:
            body = {}
        return {
            "id": body.get("id") or f"evt_mock_{uuid4().hex[:12]}",
            "type": body.get("type") or "checkout.session.completed",
            "data": body.get("data")
            or {
                "object": {
                    "customer_email": body.get("customer_email"),
                    "amount_total": settings.consumer_price_cents,
                    "customer": f"cus_mock_{uuid4().hex[:8]}",
                    "subscription": f"sub_mock_{uuid4().hex[:8]}",
                }
            },
            "mock": True,
        }

    import stripe

    stripe.api_key = settings.stripe_secret_key
    try:
        event = stripe.Webhook.construct_event(
            payload, signature or "", settings.stripe_webhook_secret
        )
        return dict(event)
    except Exception as exc:
        logger.warning("Stripe webhook verification failed: %s", exc)
        raise
