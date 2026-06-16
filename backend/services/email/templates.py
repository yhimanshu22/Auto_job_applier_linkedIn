"""HTML and plain-text templates for transactional email."""

from __future__ import annotations

from html import escape

from services.email.config import (
    BRAND_NAME,
    LEGAL_NAME,
    REGISTERED_ADDRESS,
    SUPPORT_EMAIL,
    SUPPORT_PHONE,
    frontend_url,
)

PLAN_LABELS = {
    "free_trial": "Free Trial",
    "starter": "Starter",
    "pro": "Pro",
    "agency": "Agency",
}


def _plan_label(plan: str) -> str:
    return PLAN_LABELS.get(plan.lower(), plan.replace("_", " ").title())


def _layout(*, title: str, body_html: str) -> str:
    site = escape(frontend_url())
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{escape(title)}</title></head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:Arial,sans-serif;color:#18181b;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;">
        <tr><td style="padding:28px 32px;background:#18181b;color:#ffffff;">
          <h1 style="margin:0;font-size:22px;">{escape(BRAND_NAME)}</h1>
        </td></tr>
        <tr><td style="padding:32px;">{body_html}</td></tr>
        <tr><td style="padding:20px 32px;background:#fafafa;border-top:1px solid #e4e4e7;font-size:12px;color:#71717a;">
          <p style="margin:0 0 8px;">{escape(LEGAL_NAME)} · {escape(REGISTERED_ADDRESS)}</p>
          <p style="margin:0;">Support: <a href="mailto:{escape(SUPPORT_EMAIL)}">{escape(SUPPORT_EMAIL)}</a> · {escape(SUPPORT_PHONE)}</p>
          <p style="margin:8px 0 0;"><a href="{site}">{site}</a></p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _button(label: str, href: str) -> str:
    return (
        f'<p style="margin:24px 0;">'
        f'<a href="{escape(href)}" style="display:inline-block;background:#18181b;color:#ffffff;'
        f'text-decoration:none;padding:12px 20px;border-radius:8px;font-weight:600;">'
        f"{escape(label)}</a></p>"
    )


def welcome_email(*, name: str) -> tuple[str, str, str]:
    subject = f"Welcome to {BRAND_NAME}"
    dashboard = f"{frontend_url()}/dashboard"
    text = (
        f"Hi {name},\n\n"
        f"Welcome to {BRAND_NAME}! Your account is ready.\n\n"
        f"Open your dashboard to connect LinkedIn, set job filters, and start applying:\n"
        f"{dashboard}\n\n"
        f"Need help? Reply to this email or contact {SUPPORT_EMAIL}.\n"
    )
    body = (
        f"<p>Hi <strong>{escape(name)}</strong>,</p>"
        f"<p>Welcome to <strong>{escape(BRAND_NAME)}</strong>. Your account is ready.</p>"
        f"<p>Open your dashboard to connect LinkedIn, set job filters, and start applying.</p>"
        f"{_button('Open dashboard', dashboard)}"
        f"<p style='color:#71717a;font-size:14px;'>Need help? Contact "
        f"<a href='mailto:{escape(SUPPORT_EMAIL)}'>{escape(SUPPORT_EMAIL)}</a>.</p>"
    )
    return subject, text, _layout(title=subject, body_html=body)


def trial_started_email(*, name: str, expires_at: str) -> tuple[str, str, str]:
    subject = f"Your {BRAND_NAME} free trial has started"
    dashboard = f"{frontend_url()}/dashboard"
    text = (
        f"Hi {name},\n\n"
        f"Your 24-hour free trial is active until {expires_at}.\n\n"
        f"During the trial you can use 1 LinkedIn account and up to 10 applications.\n\n"
        f"Get started: {dashboard}\n"
    )
    body = (
        f"<p>Hi <strong>{escape(name)}</strong>,</p>"
        f"<p>Your <strong>24-hour free trial</strong> is active until "
        f"<strong>{escape(expires_at)}</strong>.</p>"
        f"<p>During the trial you can use 1 LinkedIn account and up to 10 applications.</p>"
        f"{_button('Start applying', dashboard)}"
    )
    return subject, text, _layout(title=subject, body_html=body)


def payment_receipt_email(
    *,
    name: str,
    plan: str,
    billing_cycle: str,
    amount: str,
    currency: str,
    transaction_id: str,
    payment_provider: str,
    period_end: str | None = None,
) -> tuple[str, str, str]:
    plan_label = _plan_label(plan)
    cycle_label = "Yearly" if billing_cycle == "yearly" else "Monthly"
    subject = f"Payment receipt — {BRAND_NAME} {plan_label}"
    billing_url = f"{frontend_url()}/dashboard/billing"

    period_line = f"\nValid until: {period_end}" if period_end else ""
    period_html = (
        f"<tr><td style='padding:8px 0;color:#71717a;'>Valid until</td>"
        f"<td style='padding:8px 0;text-align:right;'>{escape(period_end)}</td></tr>"
        if period_end
        else ""
    )

    text = (
        f"Hi {name},\n\n"
        f"Thank you for your payment. This email is your receipt.\n\n"
        f"Plan: {plan_label} ({cycle_label})\n"
        f"Amount: {currency} {amount}\n"
        f"Transaction ID: {transaction_id}\n"
        f"Payment method: {payment_provider}{period_line}\n\n"
        f"View billing: {billing_url}\n"
    )
    body = (
        f"<p>Hi <strong>{escape(name)}</strong>,</p>"
        f"<p>Thank you for your payment. This email is your receipt.</p>"
        f"<table width='100%' style='margin:16px 0;font-size:15px;'>"
        f"<tr><td style='padding:8px 0;color:#71717a;'>Plan</td>"
        f"<td style='padding:8px 0;text-align:right;'>{escape(plan_label)} ({escape(cycle_label)})</td></tr>"
        f"<tr><td style='padding:8px 0;color:#71717a;'>Amount</td>"
        f"<td style='padding:8px 0;text-align:right;'>{escape(currency)} {escape(amount)}</td></tr>"
        f"<tr><td style='padding:8px 0;color:#71717a;'>Transaction ID</td>"
        f"<td style='padding:8px 0;text-align:right;'>{escape(transaction_id)}</td></tr>"
        f"<tr><td style='padding:8px 0;color:#71717a;'>Payment method</td>"
        f"<td style='padding:8px 0;text-align:right;'>{escape(payment_provider)}</td></tr>"
        f"{period_html}"
        f"</table>"
        f"{_button('View billing', billing_url)}"
    )
    return subject, text, _layout(title=subject, body_html=body)


def subscription_cancelled_email(*, name: str, plan: str) -> tuple[str, str, str]:
    plan_label = _plan_label(plan)
    subject = f"Your {BRAND_NAME} subscription was cancelled"
    pricing = f"{frontend_url()}/pricing"
    text = (
        f"Hi {name},\n\n"
        f"Your {plan_label} subscription has been cancelled.\n\n"
        f"You can resubscribe any time: {pricing}\n"
    )
    body = (
        f"<p>Hi <strong>{escape(name)}</strong>,</p>"
        f"<p>Your <strong>{escape(plan_label)}</strong> subscription has been cancelled.</p>"
        f"<p>You can resubscribe any time if you want to continue automating applications.</p>"
        f"{_button('View plans', pricing)}"
    )
    return subject, text, _layout(title=subject, body_html=body)


def payment_failed_email(*, name: str, plan: str) -> tuple[str, str, str]:
    plan_label = _plan_label(plan)
    subject = f"Action required — {BRAND_NAME} payment failed"
    billing_url = f"{frontend_url()}/dashboard/billing"
    text = (
        f"Hi {name},\n\n"
        f"We could not process your payment for the {plan_label} plan.\n\n"
        f"Please update your billing details to avoid interruption:\n{billing_url}\n"
    )
    body = (
        f"<p>Hi <strong>{escape(name)}</strong>,</p>"
        f"<p>We could not process your payment for the <strong>{escape(plan_label)}</strong> plan.</p>"
        f"<p>Please update your billing details to avoid interruption.</p>"
        f"{_button('Update billing', billing_url)}"
    )
    return subject, text, _layout(title=subject, body_html=body)


def community_notification_email(*, name: str, message: str) -> tuple[str, str, str]:
    subject = f"New community post from {name}"
    text = f"New community post\n\nName: {name}\n\nMessage:\n{message}\n"
    body = (
        f"<p><strong>New community post</strong></p>"
        f"<p>From: {escape(name)}</p>"
        f"<p style='white-space:pre-wrap;'>{escape(message)}</p>"
    )
    return subject, text, _layout(title=subject, body_html=body)


def feedback_notification_email(
    *,
    name: str,
    email: str,
    message: str,
    rating: int | None = None,
) -> tuple[str, str, str]:
    subject = f"Feedback from {name}"
    rating_line = f"Rating: {rating}/5\n\n" if rating else ""
    rating_html = (
        f"<p>Rating: <strong>{rating}/5</strong></p>" if rating else ""
    )
    text = (
        f"New feedback\n\nName: {name}\nEmail: {email}\n\n{rating_line}Message:\n{message}\n"
    )
    body = (
        f"<p><strong>New feedback</strong></p>"
        f"<p>Name: {escape(name)}<br>Email: {escape(email)}</p>"
        f"{rating_html}"
        f"<p style='white-space:pre-wrap;'>{escape(message)}</p>"
    )
    return subject, text, _layout(title=subject, body_html=body)
