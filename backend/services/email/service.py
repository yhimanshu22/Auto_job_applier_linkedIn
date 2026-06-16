"""High-level transactional email API."""

from __future__ import annotations

import logging

from services.email import templates
from services.email.config import DEFAULT_NOTIFY_EMAIL
from services.email.transport import send_email

log = logging.getLogger(__name__)


def _display_name(email: str, firstname: str | None = None) -> str:
    if firstname and firstname.strip():
        return firstname.strip()
    local = (email or "there").split("@", 1)[0]
    return local.replace(".", " ").replace("_", " ").title() or "there"


def _safe_send(*, to: str, subject: str, text: str, html: str, reply_to: str | None = None) -> bool:
    try:
        return send_email(to=to, subject=subject, text=text, html=html, reply_to=reply_to)
    except Exception:
        log.exception("Transactional email failed: %s -> %s", subject, to)
        return False


def send_welcome(*, email: str, name: str | None = None) -> bool:
    subject, text, html = templates.welcome_email(name=_display_name(email, name))
    return _safe_send(to=email, subject=subject, text=text, html=html)


def send_trial_started(*, email: str, expires_at: str, name: str | None = None) -> bool:
    subject, text, html = templates.trial_started_email(
        name=_display_name(email, name),
        expires_at=expires_at,
    )
    return _safe_send(to=email, subject=subject, text=text, html=html)


def send_payment_receipt(
    *,
    email: str,
    plan: str,
    billing_cycle: str,
    amount: str,
    currency: str,
    transaction_id: str,
    payment_provider: str,
    period_end: str | None = None,
    name: str | None = None,
) -> bool:
    subject, text, html = templates.payment_receipt_email(
        name=_display_name(email, name),
        plan=plan,
        billing_cycle=billing_cycle,
        amount=amount,
        currency=currency,
        transaction_id=transaction_id,
        payment_provider=payment_provider,
        period_end=period_end,
    )
    return _safe_send(to=email, subject=subject, text=text, html=html)


def send_subscription_cancelled(*, email: str, plan: str, name: str | None = None) -> bool:
    subject, text, html = templates.subscription_cancelled_email(
        name=_display_name(email, name),
        plan=plan,
    )
    return _safe_send(to=email, subject=subject, text=text, html=html)


def send_payment_failed(*, email: str, plan: str, name: str | None = None) -> bool:
    subject, text, html = templates.payment_failed_email(
        name=_display_name(email, name),
        plan=plan,
    )
    return _safe_send(to=email, subject=subject, text=text, html=html)


def send_community_notification(*, name: str, message: str) -> bool:
    subject, text, html = templates.community_notification_email(name=name, message=message)
    return _safe_send(to=DEFAULT_NOTIFY_EMAIL, subject=subject, text=text, html=html)


def send_feedback_email(
    *,
    name: str,
    email: str,
    message: str,
    rating: int | None = None,
) -> bool:
    subject, text, html = templates.feedback_notification_email(
        name=name,
        email=email,
        message=message,
        rating=rating,
    )
    return _safe_send(
        to=DEFAULT_NOTIFY_EMAIL,
        subject=subject,
        text=text,
        html=html,
        reply_to=email,
    )
