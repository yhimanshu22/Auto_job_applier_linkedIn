"""Brand and SMTP configuration for transactional email."""

from __future__ import annotations

import os

BRAND_NAME = "LinkdApply"
LEGAL_NAME = "Himanshu Yadav"
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "himu09854@gmail.com").strip()
SUPPORT_PHONE = "+91 81142 45060"
REGISTERED_ADDRESS = (
    "Pindari, Mohammadabad, District Ghazipur, Uttar Pradesh - 233222, India"
)

DEFAULT_NOTIFY_EMAIL = os.getenv("FEEDBACK_NOTIFY_EMAIL", SUPPORT_EMAIL).strip()


def frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")


def smtp_configured() -> bool:
    return bool(
        os.getenv("SMTP_HOST", "").strip()
        and os.getenv("SMTP_USER", "").strip()
        and os.getenv("SMTP_PASSWORD", "").strip()
    )


def smtp_from_address() -> str:
    return os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "")).strip()
