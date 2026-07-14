"""Stripe payment routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.db.schemas import CheckoutSessionResponse, SubscriptionStatus
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = payment_service.start_checkout(db, user)
    return CheckoutSessionResponse(
        checkout_url=result["checkout_url"],
        session_id=result["session_id"],
        mock=bool(result.get("mock")),
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: Optional[str] = Header(default=None, alias="Stripe-Signature"),
):
    payload = await request.body()
    return payment_service.handle_webhook(db, payload, stripe_signature)


@router.get("/subscription-status", response_model=SubscriptionStatus)
def subscription_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return SubscriptionStatus(**payment_service.get_subscription_status(db, user))
