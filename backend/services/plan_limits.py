"""Subscription plan caps for bot start (same rules as legacy server.assert_can_start_bot)."""

from datetime import datetime

from fastapi import HTTPException

from db_manager import db

from services.linkedin_env import (
    count_linkedin_accounts,
    preview_env_with_dashboard_credentials,
)

PLAN_LIMITS = {
    "free_trial": {
        "max_accounts": 1,
        "max_active_bots": 1,
        "monthly_applications": 10,
        "trial_hours": 24,
        "ai_answers": False,
        "priority_support": False,
        "export_history": False,
    },
    "starter": {
        "max_accounts": 1,
        "max_active_bots": 1,
        "monthly_applications": 100,
        "ai_answers": False,
        "priority_support": False,
        "export_history": False,
    },
    "pro": {
        "max_accounts": 3,
        "max_active_bots": 2,
        "monthly_applications": 500,
        "ai_answers": True,
        "priority_support": True,
        "export_history": True,
    },
    "agency": {
        "max_accounts": 10,
        "max_active_bots": 5,
        "monthly_applications": 3000,
        "ai_answers": True,
        "priority_support": True,
        "export_history": True,
    },
}


def assert_can_start_bot(user_id: str) -> None:
    # Administrative Bypass for Project Admin
    if user_id in ["himu09854@gmail.com", "local-user"]:
        return

    subscription = db.get_user_subscription(user_id)

    if not subscription or subscription["status"] not in ["active", "trialing"]:
        raise HTTPException(
            status_code=402,
            detail="Active subscription or trial required to start the bot",
        )

    # Check for trial expiration
    if subscription["status"] == "trialing" and subscription.get("current_period_end"):
        is_expired = False
        try:
            expiry = datetime.fromisoformat(subscription["current_period_end"])
            if datetime.utcnow() > expiry:
                is_expired = True
        except Exception as e:
            print(f"Error checking trial expiry: {e}")

        if is_expired:
            db.upsert_subscription(user_id=user_id, status="expired")
            raise HTTPException(
                status_code=402,
                detail="Your 24-hour free trial has expired. Please upgrade to a paid plan to continue.",
            )

    plan = subscription.get("plan", "free_trial")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free_trial"])

    probe_env = preview_env_with_dashboard_credentials()
    account_total = count_linkedin_accounts(probe_env)

    if account_total > limits["max_accounts"]:
        raise HTTPException(
            status_code=403,
            detail=f"Your '{plan}' plan allows only {limits['max_accounts']} LinkedIn account(s). You have {account_total} configured.",
        )

    if account_total == 0:
        raise HTTPException(
            status_code=400,
            detail="No LinkedIn accounts configured. Save credentials under Dashboard → secrets (LinkedIn) or set LINKEDIN_* in your environment.",
        )

    applied_this_month = db.get_monthly_application_count(user_id)
    if applied_this_month >= limits["monthly_applications"]:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly application limit reached ({applied_this_month}/{limits['monthly_applications']}). Please upgrade your plan.",
        )

    if account_total > limits["max_active_bots"]:
        raise HTTPException(
            status_code=403,
            detail=f"Your '{plan}' plan allows only {limits['max_active_bots']} active bot(s). Please reduce your active accounts.",
        )
