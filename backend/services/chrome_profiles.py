"""Shared Chrome user-data-dir paths for the job bot and LinkedIn automation."""

from __future__ import annotations

import os

from app_paths import get_runtime_writable_root
from services.chrome_ports import account_port_for_bot_id
from services.linkedin_env import _legacy_linkedin_keys_from_secrets, _iter_linkedin_key_accounts, _load_secrets


def _safe_profile_tag(bot_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in str(bot_id))[:120]


def bot_chrome_profile_dir(bot_id: str) -> str:
    """Same path convention as ``modules/open_chrome.py`` (``chrome_profiles/{BOT_ID}``)."""
    return os.path.normpath(
        os.path.join(get_runtime_writable_root(), "chrome_profiles", _safe_profile_tag(bot_id))
    )


def linkedin_email_to_bot_id(*, user_id: str, linkedin_email: str) -> str | None:
    """Map a LinkedIn login email to the supervisor ``BOT_ID`` / profile folder name."""
    needle = (linkedin_email or "").strip().lower()
    if not needle:
        return None

    legacy_keys = _legacy_linkedin_keys_from_secrets(_load_secrets(user_id=user_id))
    for username, _password, is_primary in _iter_linkedin_key_accounts(legacy_keys):
        if username.lower() != needle:
            continue
        if is_primary:
            return "main"
        for env_key, env_val in legacy_keys.items():
            if (
                env_key.startswith("LINKEDIN_USERNAME_")
                and str(env_val).strip().lower() == needle
            ):
                return env_key[len("LINKEDIN_USERNAME_") :]
        return "1"
    return None


def clear_chrome_profile_locks(profile_dir: str) -> None:
    """Remove stale singleton locks left by crashed Chrome sessions."""
    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        path = os.path.join(profile_dir, name)
        if os.path.lexists(path):
            try:
                os.remove(path)
            except OSError:
                pass


def resolve_automation_chrome_profile(
    *, user_id: str, linkedin_email: str
) -> dict[str, str] | None:
    """
    Return bot chrome profile metadata when the job bot has already created it.

    Automation reuses the on-disk session (cookies, local storage) from
    ``chrome_profiles/{BOT_ID}`` instead of the separate ``user_sessions`` cookie DB.
    """
    bot_id = linkedin_email_to_bot_id(user_id=user_id, linkedin_email=linkedin_email)
    if not bot_id:
        return None
    profile_dir = bot_chrome_profile_dir(bot_id)
    if not os.path.isdir(profile_dir):
        return None
    return {
        "bot_id": bot_id,
        "profile_dir": profile_dir,
        "debug_port": str(account_port_for_bot_id(bot_id)),
    }


def apply_automation_chrome_profile_env(env: dict, *, user_id: str, linkedin_email: str) -> bool:
    """Set env vars so the automation subprocess launches Chrome with the bot profile."""
    resolved = resolve_automation_chrome_profile(
        user_id=user_id, linkedin_email=linkedin_email
    )
    if not resolved:
        return False
    env["LINKDAPPLY_CHROME_PROFILE_DIR"] = resolved["profile_dir"]
    env["BOT_ID"] = resolved["bot_id"]
    env["CHROME_DEBUG_PORT"] = resolved["debug_port"]
    return True
