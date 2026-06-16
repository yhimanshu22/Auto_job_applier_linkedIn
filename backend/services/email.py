"""Send transactional email via SMTP (optional — skipped when not configured)."""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger(__name__)

DEFAULT_NOTIFY_EMAIL = "himu09854@gmail.com"


def _smtp_configured() -> bool:
    return bool(
        os.getenv("SMTP_HOST", "").strip()
        and os.getenv("SMTP_USER", "").strip()
        and os.getenv("SMTP_PASSWORD", "").strip()
    )


def send_feedback_email(
    *,
    name: str,
    email: str,
    message: str,
    rating: int | None = None,
) -> bool:
    """Email feedback to the team. Returns True when sent, False when SMTP is not configured."""
    if not _smtp_configured():
        log.info("SMTP not configured; feedback stored only (from %s)", email)
        return False

    to_addr = os.getenv("FEEDBACK_NOTIFY_EMAIL", DEFAULT_NOTIFY_EMAIL).strip()
    from_addr = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "")).strip()
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()

    subject = f"LinkdApply feedback from {name}"
    rating_line = f"Rating: {rating}/5\n\n" if rating else ""
    body = (
        f"New community feedback\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"{rating_line}"
        f"Message:\n{message}\n"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Reply-To"] = email
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception:
        log.exception("Failed to send feedback email from %s", email)
        raise
