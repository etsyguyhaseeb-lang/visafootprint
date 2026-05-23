import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from backend.database import AsyncSessionLocal
from backend.models import PaidOrder
from backend.email_utils import send_email, payment_confirmed_html

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


@router.get("/check-paid")
async def check_paid(email: str):
    """Look up whether an email has a paid order. Used to restore tier after navigation."""
    if not email or "@" not in email:
        return {"paid": False, "tier": None}
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PaidOrder)
            .where(PaidOrder.email == email.lower().strip())
            .where(PaidOrder.paid == True)
            .order_by(PaidOrder.created_at.desc())
        )
        order = result.scalars().first()
        if order:
            return {"paid": True, "tier": order.tier, "session_id": order.stripe_session_id}
    return {"paid": False, "tier": None}


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

        is_new = False
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
                is_new = True

        print(f"[STRIPE] Payment recorded: {session_id} tier={tier} email={email}", flush=True)

        # Update lead_status on all submissions by this email
        if is_new and email:
            from backend.models import Submission
            async with AsyncSessionLocal() as db2:
                result = await db2.execute(
                    select(Submission).where(Submission.email == email.lower().strip())
                )
                for sub in result.scalars().all():
                    sub.lead_status = "paid"
                    sub.tier        = tier
                await db2.commit()

        if is_new and email:
            screen_url = f"{FRONTEND_URL}/screen?session_id={session_id}"
            await send_email(
                to=email,
                subject="VisaFootprint — payment confirmed, start your screening",
                html=payment_confirmed_html(tier, screen_url),
            )

    return {"received": True}
