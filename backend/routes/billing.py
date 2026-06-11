import os
import stripe
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from dotenv import load_dotenv
from db_manager import db
from utils.user_resolution import resolve_user_id

load_dotenv()

router = APIRouter(prefix="/api/billing", tags=["billing"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

PRICE_MAP = {
    "monthly": {
        "starter": os.getenv("STRIPE_PRICE_STARTER_MONTHLY"),
        "pro": os.getenv("STRIPE_PRICE_PRO_MONTHLY"),
        "agency": os.getenv("STRIPE_PRICE_AGENCY_MONTHLY"),
    },
    "yearly": {
        "starter": os.getenv("STRIPE_PRICE_STARTER_YEARLY"),
        "pro": os.getenv("STRIPE_PRICE_PRO_YEARLY"),
        "agency": os.getenv("STRIPE_PRICE_AGENCY_YEARLY"),
    },
}


from typing import Literal

class CheckoutRequest(BaseModel):
    plan: Literal["starter", "pro", "agency"]
    billing_cycle: Literal["monthly", "yearly"] = "monthly"
    user_id: str
    email: str


@router.post("/create-checkout-session")
async def create_checkout_session(payload: CheckoutRequest, request: Request):
    # The verified session (when present) decides which account gets the plan.
    user_id = await resolve_user_id(request, payload.user_id)
    price_id = PRICE_MAP.get(payload.billing_cycle, {}).get(payload.plan)

    if not price_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid plan or billing cycle selected",
        )

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            customer_email=payload.email,
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            success_url=f"{FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/billing/cancel",
            metadata={
                "user_id": user_id,
                "plan": payload.plan,
                "billing_cycle": payload.billing_cycle,
            },
            subscription_data={
                "metadata": {
                    "user_id": user_id,
                    "plan": payload.plan,
                    "billing_cycle": payload.billing_cycle,
                }
            },
        )

        return {"url": session.url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FreeTrialRequest(BaseModel):
    user_id: str = "local-user"


@router.post("/start-free-trial")
async def start_free_trial(payload: FreeTrialRequest, request: Request):
    user_id = await resolve_user_id(request, payload.user_id)
    # Check if user already has/had a trial or paid plan
    sub = db.get_user_subscription(user_id)
    
    if sub and sub.get("plan") != "free":
        # If they already have a plan (trial or paid), don't allow another trial
        raise HTTPException(
            status_code=400, 
            detail="You have already used your trial or have an active plan."
        )

    # Set trial to expire in 24 hours
    expiry = datetime.utcnow() + timedelta(hours=24)
    
    try:
        db.upsert_subscription(
            user_id=user_id,
            plan="free_trial",
            status="trialing",
            current_period_end=expiry.isoformat()
        )
        return {"status": "success", "expires_at": expiry.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        handle_checkout_completed(data)

    elif event_type == "customer.subscription.created":
        handle_subscription_updated(data)

    elif event_type == "customer.subscription.updated":
        handle_subscription_updated(data)

    elif event_type == "customer.subscription.deleted":
        handle_subscription_deleted(data)

    elif event_type == "invoice.payment_failed":
        handle_payment_failed(data)

    return {"received": True}


def handle_checkout_completed(session):
    try:
        metadata = getattr(session, "metadata", {})
        user_id = metadata.get("user_id")
        plan = metadata.get("plan")
        billing_cycle = metadata.get("billing_cycle", "monthly")
        customer_id = getattr(session, "customer", None)
        subscription_id = getattr(session, "subscription", None)

        print(f"DEBUG: Processing checkout for user: {user_id}, plan: {plan}, cycle: {billing_cycle}")

        if user_id:
            db.upsert_subscription(
                user_id=user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                plan=plan,
                billing_cycle=billing_cycle,
                status='active'
            )
        else:
            print("WARNING: No user_id found in checkout session metadata. Skip DB update.")
    except Exception as e:
        print(f"ERROR in handle_checkout_completed: {e}")
        raise e


def handle_subscription_updated(subscription):
    try:
        metadata = getattr(subscription, "metadata", {})
        user_id = metadata.get("user_id")
        plan = metadata.get("plan")
        billing_cycle = metadata.get("billing_cycle", "monthly")
        
        status = getattr(subscription, "status", "inactive")
        subscription_id = getattr(subscription, "id", None)
        customer_id = getattr(subscription, "customer", None)
        cancel_at_period_end = getattr(subscription, "cancel_at_period_end", False)

        items = getattr(subscription, "items", {}).get("data", [])
        price_id = items[0]["price"]["id"] if items else None
        current_period_end = getattr(subscription, "current_period_end", None)

        print(f"DEBUG: Subscription updated: user={user_id}, plan={plan}, cycle={billing_cycle}, status={status}")

        if user_id:
            db.upsert_subscription(
                user_id=user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                stripe_price_id=price_id,
                plan=plan,
                billing_cycle=billing_cycle,
                status=status,
                current_period_end=current_period_end,
                cancel_at_period_end=1 if cancel_at_period_end else 0
            )
    except Exception as e:
        print(f"ERROR in handle_subscription_updated: {e}")
        raise e


def handle_subscription_deleted(subscription):
    subscription_id = subscription.get("id")
    user_id = subscription.get("metadata", {}).get("user_id")

    print("Subscription deleted:", subscription_id)

    if user_id:
        db.upsert_subscription(
            user_id=user_id,
            status='canceled'
        )


def handle_payment_failed(invoice):
    customer_id = invoice.get("customer")
    print("Payment failed:", customer_id)
    # Could mark as past_due here if we query the user by customer_id
    # For now, subscription.updated event usually covers this anyway


class PortalRequest(BaseModel):
    user_id: str = "local-user"

ADMIN_EMAILS = ["himu09854@gmail.com", "local-user"]

@router.get("/subscription")
async def get_subscription(request: Request, user_id: str = "local-user"):
    user_id = await resolve_user_id(request, user_id)
    # Administrative Bypass for Project Admin
    if user_id in ["himu09854@gmail.com", "local-user"]:
        return {
            "plan": "agency",
            "status": "active",
            "current_period_end": 4102444800,  # Far future (Year 2100)
            "billing_cycle": "yearly",
            "limit": 3000
        }
        
    sub = db.get_user_subscription(user_id)
    if not sub:
        return {"plan": "free", "status": "inactive", "limit": 0}
    return sub


@router.post("/create-portal-session")
async def create_portal_session(payload: PortalRequest, request: Request):
    user_id = await resolve_user_id(request, payload.user_id)
    try:
        sub = db.get_user_subscription(user_id)
        if not sub or not sub.get("stripe_customer_id"):
            raise HTTPException(status_code=400, detail="No active Stripe customer found for this user.")

        session = stripe.billing_portal.Session.create(
            customer=sub["stripe_customer_id"],
            return_url=f"{FRONTEND_URL}/settings/billing",
        )

        return {"url": session.url}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
