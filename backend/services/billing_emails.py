"""Send billing and onboarding emails (non-blocking)."""

from __future__ import annotations

import logging
from datetime import datetime


from services.email import (
    send_payment_failed,
    send_payment_receipt,
    send_subscription_cancelled,
    send_trial_started,
    send_welcome,
)

log = logging.getLogger(__name__)


def _format_period_end(value: str | int | float | None) -> str | None:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(value).strftime("%d %b %Y")
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%d %b %Y")
    except Exception:
        return str(value)


def notify_onboarding_and_trial(*, email: str, expires_at: str) -> None:
    send_welcome(email=email)
    send_trial_started(email=email, expires_at=_format_period_end(expires_at) or expires_at)




def notify_stripe_checkout(*, session: dict) -> None:
    metadata = session.get("metadata", {}) or {}
    email = session.get("customer_email")
    if not email:
        details = session.get("customer_details")
        if details is not None:
            email = details.get("email")
    if not email:
        candidate = metadata.get("user_id")
        email = candidate if candidate and "@" in candidate else None
    if not email:
        return

    plan = metadata.get("plan") or "starter"
    billing_cycle = metadata.get("billing_cycle") or "monthly"
    session_id = session.get("id") or "—"
    amount_total = session.get("amount_total")
    currency = (session.get("currency") or "usd").upper()
    amount = f"{amount_total / 100:.2f}" if amount_total else "—"

    send_payment_receipt(
        email=str(email),
        plan=plan,
        billing_cycle=billing_cycle,
        amount=amount,
        currency=currency,
        transaction_id=str(session_id),
        payment_provider="Stripe",
    )


def notify_subscription_cancelled(*, email: str, plan: str) -> None:
    if not email or "@" not in email:
        return
    send_subscription_cancelled(email=email, plan=plan)


def notify_payment_failed(*, email: str, plan: str) -> None:
    if not email or "@" not in email:
        return
    send_payment_failed(email=email, plan=plan)
