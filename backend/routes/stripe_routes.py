import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from backend.database import AsyncSessionLocal
from backend.models import PaidOrder

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL   = os.getenv("FRONTEND_URL", "https://visafootprint.com").rstrip("/")

PRICE_IDS = {
    "standard": os.getenv("STRIPE_PRICE_STANDARD", ""),
    "attorney": os.getenv("STRIPE_PRICE_ATTORNEY", ""),
    "monitor":  os.getenv("STRIPE_PRICE_MONITOR",  ""),
}

TIER_MODES = {
    "standard": "payment",
    "attorney": "payment",
    "monitor":  "subscription",
}


class CheckoutRequest(BaseModel):
    tier: str


@router.post("/checkout")
async def create_checkout(req: CheckoutRequest):
    tier = req.tier.lower()
    price_id = PRICE_IDS.get(tier)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan selected.")
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Payment not configured.")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode=TIER_MODES[tier],
            success_url=f"{FRONTEND_URL}/screen?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/#pricing",
            metadata={"tier": tier},
        )
        return {"checkout_url": session.url}
    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify-payment")
async def verify_payment(session_id: str):
    if not session_id or not stripe.api_key:
        return {"paid": False, "tier": None}
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        paid = session.payment_status == "paid" or session.status == "complete"
        tier = (session.metadata or {}).get("tier", "standard")
        return {"paid": paid, "tier": tier if paid else None}
    except Exception:
        raise HTTPException(status_code=400, detail="Could not verify payment session.")


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")
    except Exception:
        raise HTTPException(status_code=400, detail="Webhook error.")

    if event["type"] == "checkout.session.completed":
        session   = event["data"]["object"]
        tier      = (session.get("metadata") or {}).get("tier", "standard")
        email     = (session.get("customer_details") or {}).get("email", "")
        session_id = session.get("id", "")

        async with AsyncSessionLocal() as db:
            existing = await db.execute(
                select(PaidOrder).where(PaidOrder.stripe_session_id == session_id)
            )
            if not existing.scalar_one_or_none():
                db.add(PaidOrder(
                    stripe_session_id=session_id,
                    email=email,
                    tier=tier,
                    paid=True,
                ))
                await db.commit()

        print(f"[STRIPE] Payment recorded: {session_id} tier={tier} email={email}", flush=True)

    return {"received": True}
