import os
import stripe
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from dotenv import load_dotenv
from db_manager import db
from utils.user_resolution import resolve_user_id
from services.plan_limits import PLAN_LIMITS
from services import payu as payu_service

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


class PayUInitiateRequest(BaseModel):
    plan: Literal["starter", "pro", "agency"]
    billing_cycle: Literal["monthly", "yearly"] = "monthly"
    user_id: str
    email: str
    firstname: str | None = None
    phone: str | None = None


@router.post("/payu/initiate")
async def initiate_payu_payment(payload: PayUInitiateRequest, request: Request):
    if not payu_service.is_payu_configured():
        raise HTTPException(
            status_code=503,
            detail="PayU is not configured. Set PAYU_MERCHANT_KEY and PAYU_MERCHANT_SALT.",
        )

    user_id = await resolve_user_id(request, payload.user_id)

    try:
        params = payu_service.build_payment_params(
            user_id=user_id,
            email=payload.email,
            plan=payload.plan,
            billing_cycle=payload.billing_cycle,
            success_url=f"{BACKEND_PUBLIC_URL}/api/billing/payu/callback/success",
            failure_url=f"{BACKEND_PUBLIC_URL}/api/billing/payu/callback/failure",
            firstname=payload.firstname,
            phone=payload.phone,
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return {
        "action": payu_service.payu_payment_url(),
        "params": params,
    }


def _activate_payu_subscription(params: dict[str, str]) -> bool:
    user_id = params.get("udf1")
    plan = params.get("udf2")
    billing_cycle = params.get("udf3", "monthly")
    txnid = params.get("txnid")

    if not user_id or plan not in payu_service.PLAN_LABELS:
        print("WARNING: PayU callback missing user_id or plan in UDF fields")
        return False

    expected_amount = payu_service.get_inr_amount(plan, billing_cycle)  # type: ignore[arg-type]
    if params.get("amount") != expected_amount:
        print(
            f"WARNING: PayU amount mismatch for {txnid}: "
            f"expected {expected_amount}, got {params.get('amount')}"
        )
        return False

    period_end = payu_service.period_end_for_cycle(billing_cycle)  # type: ignore[arg-type]
    db.upsert_subscription(
        user_id=user_id,
        plan=plan,
        billing_cycle=billing_cycle,
        status="active",
        payment_provider="payu",
        payu_txnid=txnid,
        current_period_end=period_end,
        cancel_at_period_end=0,
    )
    return True


async def _handle_payu_callback(request: Request, *, success: bool):
    form = await request.form()
    params = {k: str(v) for k, v in form.items()}
    salt = os.getenv("PAYU_MERCHANT_SALT", "")

    if not payu_service.verify_response_hash(params, salt):
        print(f"WARNING: PayU hash verification failed for txnid={params.get('txnid')}")
        return RedirectResponse(
            f"{FRONTEND_URL}/billing/cancel?reason=hash_verification_failed",
            status_code=303,
        )

    status = (params.get("status") or "").lower()
    txnid = params.get("txnid", "")

    if success and status == "success":
        verified = payu_service.verify_payment_with_payu(txnid)
        if verified and str(verified.get("status", "")).lower() not in ("success", "captured"):
            print(f"WARNING: PayU verify_payment status mismatch for {txnid}: {verified}")
            return RedirectResponse(
                f"{FRONTEND_URL}/billing/cancel?reason=payment_not_verified",
                status_code=303,
            )

        if not _activate_payu_subscription(params):
            return RedirectResponse(
                f"{FRONTEND_URL}/billing/cancel?reason=activation_failed",
                status_code=303,
            )
        return RedirectResponse(
            f"{FRONTEND_URL}/billing/success?provider=payu&txnid={txnid}",
            status_code=303,
        )

    return RedirectResponse(
        f"{FRONTEND_URL}/billing/cancel?reason={status or 'failed'}",
        status_code=303,
    )


@router.post("/payu/callback/success")
async def payu_callback_success(request: Request):
    return await _handle_payu_callback(request, success=True)


@router.post("/payu/callback/failure")
async def payu_callback_failure(request: Request):
    return await _handle_payu_callback(request, success=False)


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
                status='active',
                payment_provider='stripe',
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
                cancel_at_period_end=1 if cancel_at_period_end else 0,
                payment_provider='stripe',
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
    user_id: str | None = None

ADMIN_EMAILS = ["himu09854@gmail.com", "local-user"]


def _enrich_subscription(sub: dict) -> dict:
    plan = (sub.get("plan") or "free_trial").lower()
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free_trial"])
    out = dict(sub)
    out["limit"] = limits["monthly_applications"]
    out["max_accounts"] = limits["max_accounts"]
    out["max_active_bots"] = limits["max_active_bots"]
    return out


@router.get("/subscription")
async def get_subscription(request: Request, user_id: str | None = None):
    user_id = await resolve_user_id(request, user_id)
    # Administrative Bypass for Project Admin
    if user_id in ADMIN_EMAILS:
        return {
            "plan": "agency",
            "status": "active",
            "current_period_end": 4102444800,  # Far future (Year 2100)
            "billing_cycle": "yearly",
            "limit": 3000,
            "max_accounts": 10,
            "max_active_bots": 5,
        }

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
