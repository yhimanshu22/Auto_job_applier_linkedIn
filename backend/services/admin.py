"""Developer admin bypass — single source for plan and billing overrides."""

from __future__ import annotations

import os

DEVELOPER_ADMIN = "himu09854@gmail.com"


def admin_emails() -> frozenset[str]:
    emails = {DEVELOPER_ADMIN.lower()}
    extra = os.getenv("LINKDAPPLY_ADMIN_EMAILS", "").strip()
    if extra:
        for part in extra.split(","):
            part = part.strip().lower()
            if part:
                emails.add(part)
    return frozenset(emails)


def is_admin(user_id: str | None) -> bool:
    if not user_id:
        return False
    return user_id.strip().lower() in admin_emails()


def effective_plan(user_id: str, plan: str) -> str:
    return "agency" if is_admin(user_id) else plan


def admin_subscription() -> dict:
    return {
        "plan": "agency",
        "status": "active",
        "current_period_end": 4102444800,
        "billing_cycle": "yearly",
        "limit": 3000,
        "max_accounts": 10,
        "max_active_bots": 5,
    }
