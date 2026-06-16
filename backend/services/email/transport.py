"""SMTP transport for transactional email."""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

from services.email.config import smtp_configured, smtp_from_address

log = logging.getLogger(__name__)


def send_email(
    *,
    to: str,
    subject: str,
    text: str,
    html: str | None = None,
    reply_to: str | None = None,
) -> bool:
    """Send an email. Returns False when SMTP is not configured."""
    if not smtp_configured():
        log.info("SMTP not configured; skipped email to %s (%s)", to, subject)
        return False

    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    from_addr = smtp_from_address()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception:
        log.exception("Failed to send email to %s (%s)", to, subject)
        raise
