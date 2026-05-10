"""LinkedIn account discovery from DB secrets (aligned with supervisor.BotSupervisor._get_accounts)."""

import logging
import os

from db_manager import db


def apply_dashboard_linkedin_credentials(env: dict) -> None:
    """
    Inject LinkedIn credentials from DB (dashboard) into env for the supervisor / bot:
    - Primary: username + password -> LINKEDIN_USERNAME, LINKEDIN_PASSWORD
    - Additional: linkedin_extra_accounts JSON -> LINKEDIN_USERNAME_1..N, LINKEDIN_PASSWORD_1..N
    """
    try:
        secrets_cfg = db.get_all_by_category("secrets")
    except Exception:
        logging.warning("Could not read secrets from DB for LinkedIn credentials.")
        return
    user = secrets_cfg.get("username")
    password = secrets_cfg.get("password")
    if user and str(user).strip():
        env["LINKEDIN_USERNAME"] = str(user).strip()
    if password is not None and str(password).strip() != "":
        env["LINKEDIN_PASSWORD"] = str(password)

    extras = secrets_cfg.get("linkedin_extra_accounts")
    if isinstance(extras, list):
        for i, acc in enumerate(extras, start=1):
            if not isinstance(acc, dict):
                continue
            u = (acc.get("username") or "").strip()
            p = acc.get("password")
            if not u or p is None or str(p).strip() == "":
                continue
            env[f"LINKEDIN_USERNAME_{i}"] = u
            env[f"LINKEDIN_PASSWORD_{i}"] = str(p)


def preview_env_with_dashboard_credentials() -> dict:
    env = os.environ.copy()
    apply_dashboard_linkedin_credentials(env)
    return env


def count_linkedin_accounts(env: dict) -> int:
    """Match supervisor.BotSupervisor._get_accounts — count distinct runnable accounts."""
    n = 0
    du = env.get("LINKEDIN_USERNAME")
    dp = env.get("LINKEDIN_PASSWORD")
    if du and dp:
        n += 1
    for key, value in env.items():
        if key.startswith("LINKEDIN_USERNAME_") and key[18:] and value:
            suffix = key[18:]
            if env.get(f"LINKEDIN_PASSWORD_{suffix}"):
                n += 1
    return n
