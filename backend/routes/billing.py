import os
import stripe
from fastapi import APIRouter, Request, HTTPException, Query, Header
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from dotenv import load_dotenv
from db_manager import db
from services.admin import admin_subscription, is_admin
from utils.user_resolution import resolve_user_id
from services.plan_limits import PLAN_LIMITS
from services import billing_emails

load_dotenv()

router = APIRouter(prefix="/api/billing", tags=["billing"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", FRONTEND_URL).rstrip("/")

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
            allow_promotion_codes=True,
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
    user_id: str | None = None


@router.post("/start-free-trial")
async def start_free_trial(payload: FreeTrialRequest, request: Request):
    user_id = await resolve_user_id(request, payload.user_id)
    sub = db.get_user_subscription(user_id)

    if sub:
        raise HTTPException(
            status_code=400,
            detail="You have already used your trial or have an active plan.",
        )

    expiry = datetime.utcnow() + timedelta(hours=24)
    
    try:
        db.upsert_subscription(
            user_id=user_id,
            plan="free_trial",
            status="trialing",
            current_period_end=expiry.isoformat()
        )
        billing_emails.notify_onboarding_and_trial(
            email=user_id,
            expires_at=expiry.isoformat(),
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

    event_dict = event.to_dict()
    event_type = event_dict["type"]
    data = event_dict["data"]["object"]

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


def handle_checkout_completed(session: dict):
    try:
        metadata = session.get("metadata", {}) or {}
        user_id = metadata.get("user_id")
        plan = metadata.get("plan")
        billing_cycle = metadata.get("billing_cycle", "monthly")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        print(f"DEBUG: Processing checkout for user: {user_id}, plan: {plan}, cycle: {billing_cycle}")

        if user_id:
            db.upsert_subscription(
                user_id=user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                plan=plan,
                billing_cycle=billing_cycle,
                status='active',
                payment_provider='stripe',
            )
            billing_emails.notify_stripe_checkout(session=session)
        else:
            print("WARNING: No user_id found in checkout session metadata. Skip DB update.")
    except Exception as e:
        print(f"ERROR in handle_checkout_completed: {e}")
        raise e


def handle_subscription_updated(subscription: dict):
    try:
        metadata = subscription.get("metadata", {}) or {}
        user_id = metadata.get("user_id")
        plan = metadata.get("plan")
        billing_cycle = metadata.get("billing_cycle", "monthly")
        
        status = subscription.get("status", "inactive")
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")
        cancel_at_period_end = subscription.get("cancel_at_period_end", False)

        items = subscription.get("items", {}).get("data", [])
        price_id = items[0]["price"]["id"] if items else None
        current_period_end = subscription.get("current_period_end")
        if isinstance(current_period_end, (int, float)):
            from datetime import datetime
            current_period_end = datetime.utcfromtimestamp(current_period_end).isoformat()

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
                cancel_at_period_end=1 if cancel_at_period_end else 0,
                payment_provider='stripe',
            )
    except Exception as e:
        print(f"ERROR in handle_subscription_updated: {e}")
        raise e


def handle_subscription_deleted(subscription: dict):
    subscription_id = subscription.get("id")
    metadata = subscription.get("metadata", {}) or {}
    user_id = metadata.get("user_id")
    plan = metadata.get("plan") or "starter"

    print("Subscription deleted:", subscription_id)

    if user_id:
        db.upsert_subscription(
            user_id=user_id,
            status='canceled'
        )
        billing_emails.notify_subscription_cancelled(email=user_id, plan=plan)


def handle_payment_failed(invoice: dict):
    customer_id = invoice.get("customer")
    email = invoice.get("customer_email")
    plan = "starter"
    print("Payment failed:", customer_id)
    if email:
        billing_emails.notify_payment_failed(email=email, plan=plan)


class PortalRequest(BaseModel):
    user_id: str | None = None


def _enrich_subscription(sub: dict) -> dict:
    plan = (sub.get("plan") or "free_trial").lower()
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free_trial"])
    out = dict(sub)
    out["limit"] = limits["monthly_applications"]
    out["max_accounts"] = limits["max_accounts"]
    out["max_active_bots"] = limits["max_active_bots"]
    return out


@router.get("/subscription-internal")
async def get_subscription_internal(
    user_id: str = Query(...),
    x_linkdapply_key: str | None = Header(None, alias="X-LinkdApply-Key"),
):
    """Trusted lookup for the desktop sidecar (local data + cloud billing)."""
    expected = os.getenv("LINKDAPPLY_INTERNAL_KEY", "").strip()
    if not expected or x_linkdapply_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")

    uid = user_id.strip()
    if is_admin(uid):
        return admin_subscription()

    sub = db.get_user_subscription(uid)
    if not sub:
        return {"plan": "free", "status": "inactive", "limit": 0}
    return _enrich_subscription(sub)


@router.get("/subscription")
async def get_subscription(request: Request, user_id: str | None = None):
    user_id = await resolve_user_id(request, user_id)
    if is_admin(user_id):
        return admin_subscription()

    sub = db.get_user_subscription(user_id)
    if not sub:
        return {"plan": "free", "status": "inactive", "limit": 0}
    return _enrich_subscription(sub)


@router.post("/create-portal-session")
async def create_portal_session(payload: PortalRequest, request: Request):
    user_id = await resolve_user_id(request, payload.user_id)
    try:
        sub = db.get_user_subscription(user_id)
        if not sub:
            raise HTTPException(status_code=400, detail="No active subscription found for this user.")

        if sub.get("payment_provider") == "payu":
            raise HTTPException(
                status_code=400,
                detail="PayU subscriptions are managed from the pricing page. Visit /pricing to renew or change your plan.",
            )

        if not sub.get("stripe_customer_id"):
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
