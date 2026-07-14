"""Stripe-ready payment service with mock mode for local/dev."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import PaymentEvent, Subscription, User
from app.integrations.stripe_client import create_checkout_session, verify_webhook


CONSUMER_TIER = "consumer"
FREE_TIER = "free"
RESOURCE_OFFICER_TIER = "resource_officer"  # placeholder
ADMIN_TIER = "admin"  # placeholder


def get_subscription_status(db: Session, user: User) -> dict:
    settings = get_settings()
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if sub is None:
        return {
            "tier": FREE_TIER,
            "status": "active",
            "current_period_end": None,
            "price_cents": settings.consumer_price_cents,
        }
    return {
        "tier": sub.tier,
        "status": sub.status,
        "current_period_end": sub.current_period_end,
        "price_cents": settings.consumer_price_cents,
    }


def start_checkout(db: Session, user: User) -> dict:
    settings = get_settings()
    result = create_checkout_session(
        customer_email=user.email,
        customer_id=user.stripe_customer_id,
        success_url=f"{settings.frontend_url}/billing?success=1",
        cancel_url=f"{settings.frontend_url}/billing?canceled=1",
        price_cents=settings.consumer_price_cents,
    )
    db.add(
        PaymentEvent(
            user_id=user.id,
            event_type="checkout.session.created",
            stripe_event_id=result.get("session_id"),
            amount_cents=settings.consumer_price_cents,
            payload_summary={"mock": result.get("mock", False)},
        )
    )
    db.commit()
    return result


def handle_webhook(db: Session, payload: bytes, signature: Optional[str]) -> dict[str, Any]:
    event = verify_webhook(payload, signature)
    event_id = event.get("id") or f"evt_mock_{uuid4()}"
    existing = db.query(PaymentEvent).filter(PaymentEvent.stripe_event_id == event_id).first()
    if existing:
        return {"status": "duplicate"}

    event_type = event.get("type", "unknown")
    data_object = (event.get("data") or {}).get("object") or {}
    customer_email = data_object.get("customer_email")
    user = None
    if customer_email:
        user = db.query(User).filter(User.email == customer_email.lower()).first()

    payment = PaymentEvent(
        user_id=user.id if user else None,
        event_type=event_type,
        stripe_event_id=event_id,
        amount_cents=data_object.get("amount_total") or get_settings().consumer_price_cents,
        payload_summary={"type": event_type, "mock": event.get("mock", False)},
    )
    db.add(payment)

    if event_type in {"checkout.session.completed", "invoice.paid", "customer.subscription.updated"}:
        if user:
            sub = (
                db.query(Subscription)
                .filter(Subscription.user_id == user.id)
                .order_by(Subscription.created_at.desc())
                .first()
            )
            if sub is None:
                sub = Subscription(user_id=user.id)
                db.add(sub)
            sub.tier = CONSUMER_TIER
            sub.status = "active"
            sub.stripe_customer_id = data_object.get("customer") or user.stripe_customer_id
            sub.stripe_subscription_id = data_object.get("subscription") or f"sub_mock_{uuid4().hex[:12]}"
            sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
            if data_object.get("customer"):
                user.stripe_customer_id = data_object.get("customer")
            payment.subscription_id = sub.id

    db.commit()
    return {"status": "ok", "event_type": event_type}
