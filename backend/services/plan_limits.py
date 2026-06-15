"""Subscription plan caps for bot start (same rules as legacy server.assert_can_start_bot)."""

from datetime import datetime

from fastapi import HTTPException

from db_manager import db

from services.admin import is_admin
from services.cloud_billing import get_subscription_for_gating, uses_cloud_subscription
from services.linkedin_env import (
    count_linkedin_accounts,
    list_supervisor_accounts,
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
    if is_admin(user_id):
        runnable = len(list_supervisor_accounts(user_id=user_id))
        if runnable == 0:
            raise HTTPException(
                status_code=400,
                detail="No LinkedIn accounts saved. Open Dashboard → secrets, enter email and password, then click Save LinkedIn accounts.",
            )
        return

    subscription = get_subscription_for_gating(user_id)

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
            if not uses_cloud_subscription():
                db.upsert_subscription(user_id=user_id, status="expired")
            raise HTTPException(
                status_code=402,
                detail="Your 24-hour free trial has expired. Please upgrade to a paid plan to continue.",
            )

    plan = subscription.get("plan", "free_trial")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free_trial"])

    probe_env = preview_env_with_dashboard_credentials(user_id=user_id)
    account_total = count_linkedin_accounts(probe_env, user_id=user_id)
    runnable_total = len(list_supervisor_accounts(user_id=user_id))

    if account_total > limits["max_accounts"]:
        raise HTTPException(
            status_code=403,
            detail=f"Your '{plan}' plan allows only {limits['max_accounts']} LinkedIn account(s). You have {account_total} configured.",
        )

    if runnable_total == 0:
        raise HTTPException(
            status_code=400,
            detail="No LinkedIn accounts saved with a password. Open Dashboard → secrets, enter email and password, then click Save LinkedIn accounts.",
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


# ---------------------------------------------------------------------------
# Linkedln-Automation-Framework (posting / engagement) gating
# ---------------------------------------------------------------------------

# Daily ceiling on Linkedln-Automation-Framework actions per plan. Distinct
# from job-applier monthly_applications so the two automations don't compete
# for the same quota.
AUTOMATION_DAILY_LIMITS: dict[str, int] = {
    "free_trial": 5,
    "starter": 25,
    "pro": 200,
    "agency": 1000,
}


def assert_can_run_automation(user_id: str) -> None:
    """Gate the LinkedIn automation endpoints.

    Same admin bypass as ``assert_can_start_bot``, otherwise:
      * Require an active / trialing subscription (and not an expired trial).
      * Enforce a per-day count of completed-or-running automation tasks
        based on ``AUTOMATION_DAILY_LIMITS`` for the user's plan.
    """
    if is_admin(user_id):
        return

    subscription = get_subscription_for_gating(user_id)

    if not subscription or subscription["status"] not in ["active", "trialing"]:
        raise HTTPException(
            status_code=402,
            detail="Active subscription or trial required to run LinkedIn automation",
        )

    if subscription["status"] == "trialing" and subscription.get("current_period_end"):
        try:
            expiry = datetime.fromisoformat(subscription["current_period_end"])
            if datetime.utcnow() > expiry:
                if not uses_cloud_subscription():
                    db.upsert_subscription(user_id=user_id, status="expired")
                raise HTTPException(
                    status_code=402,
                    detail="Your free trial has expired. Please upgrade to a paid plan to continue.",
                )
        except HTTPException:
            raise
        except Exception as exc:
            print(f"Error checking trial expiry for automation gating: {exc}")

    plan = subscription.get("plan", "free_trial")
    daily_cap = AUTOMATION_DAILY_LIMITS.get(plan, AUTOMATION_DAILY_LIMITS["free_trial"])

    used_today = db.count_automation_tasks_today(user_id)
    if used_today >= daily_cap:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Daily automation limit reached ({used_today}/{daily_cap}) on the "
                f"'{plan}' plan. Try again tomorrow or upgrade your plan."
            ),
        )
