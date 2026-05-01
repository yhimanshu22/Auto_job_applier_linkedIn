import os
import stripe
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from db_manager import db

load_dotenv()

router = APIRouter(prefix="/api/billing", tags=["billing"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

PRICE_MAP = {
    "starter": os.getenv("STRIPE_PRICE_STARTER"),
    "pro": os.getenv("STRIPE_PRICE_PRO"),
    "agency": os.getenv("STRIPE_PRICE_AGENCY"),
}


class CheckoutRequest(BaseModel):
    plan: str
    user_id: str
    email: str


@router.post("/create-checkout-session")
async def create_checkout_session(payload: CheckoutRequest):
    price_id = PRICE_MAP.get(payload.plan)

    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan selected")

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
                "user_id": payload.user_id,
                "plan": payload.plan,
            },
            subscription_data={
                "metadata": {
                    "user_id": payload.user_id,
                    "plan": payload.plan,
                }
            },
        )

        return {"url": session.url}

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
        # Stripe objects might not have .get() in some versions, use getattr
        metadata = getattr(session, "metadata", {})
        user_id = metadata.get("user_id") if metadata else None
        plan = metadata.get("plan") if metadata else None
        customer_id = getattr(session, "customer", None)
        subscription_id = getattr(session, "subscription", None)

        print(f"DEBUG: Processing checkout for user: {user_id}, plan: {plan}")

        if user_id:
            db.upsert_subscription(
                user_id=user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                plan=plan,
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
        user_id = metadata.get("user_id") if metadata else None
        plan = metadata.get("plan") if metadata else None
        status = getattr(subscription, "status", "inactive")
        subscription_id = getattr(subscription, "id", None)
        customer_id = getattr(subscription, "customer", None)
        cancel_at_period_end = getattr(subscription, "cancel_at_period_end", False)

        items = getattr(subscription, "items", {}).get("data", [])
        price_id = items[0]["price"]["id"] if items else None
        current_period_end = getattr(subscription, "current_period_end", None)

        print(f"DEBUG: Subscription updated: user={user_id}, plan={plan}, status={status}")

        if user_id:
            db.upsert_subscription(
                user_id=user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                stripe_price_id=price_id,
                plan=plan,
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

@router.get("/subscription")
async def get_subscription(user_id: str = "local-user"):
    sub = db.get_user_subscription(user_id)
    if not sub:
        return {"plan": "free", "status": "inactive"}
    return sub


@router.post("/create-portal-session")
async def create_portal_session(payload: PortalRequest):
    try:
        sub = db.get_user_subscription(payload.user_id)
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
