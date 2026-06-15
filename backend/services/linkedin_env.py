"""LinkedIn account discovery from DB secrets (LINKEDIN_USERNAME* keys).

LinkedIn credentials are stored in the per-user ``secrets`` DB category as flat
keys (``LINKEDIN_USERNAME``, ``LINKEDIN_PASSWORD``, ``LINKEDIN_USERNAME_<n>``,
``LINKEDIN_PASSWORD_<n>``) — typically via the secrets.py code editor.

Also exposes Linkedln-Automation-Framework settings injection so dashboard-managed
AI keys, marketing mode, and project metadata are passed into the framework
subprocess at launch time.
"""

import logging
import os

from db_manager import db
from services.chrome_ports import account_port_for_slot

CANONICAL_LINKEDIN_KEYS = ("username", "password", "linkedin_extra_accounts")


def _legacy_linkedin_keys_from_secrets(secrets_cfg: dict) -> dict[str, str]:
    """``LINKEDIN_USERNAME*`` / ``LINKEDIN_PASSWORD*`` rows in secrets."""
    out: dict[str, str] = {}
    for key, value in secrets_cfg.items():
        if not isinstance(key, str) or value is None:
            continue
        if key == "LINKEDIN_USERNAME" or key.startswith("LINKEDIN_USERNAME_"):
            s = str(value).strip()
            if s:
                out[key] = s
        elif key == "LINKEDIN_PASSWORD" or key.startswith("LINKEDIN_PASSWORD_"):
            s = str(value).strip()
            if s:
                out[key] = s
    return out


def _next_linkedin_index(legacy: dict[str, str]) -> int:
    n = 1
    for key in legacy:
        if not key.startswith("LINKEDIN_USERNAME_"):
            continue
        suffix = key[len("LINKEDIN_USERNAME_") :]
        try:
            n = max(n, int(suffix) + 1)
        except ValueError:
            pass
    return n


def _email_in_legacy(legacy: dict[str, str], email: str) -> bool:
    target = email.strip().lower()
    for username, _, _ in _iter_linkedin_key_accounts(legacy):
        if username.lower() == target:
            return True
    return False


def migrate_canonical_linkedin_to_legacy(*, user_id: str) -> bool:
    """Convert deprecated username/password/linkedin_extra_accounts rows to LINKEDIN_* keys."""
    try:
        secrets_cfg = db.get_all_by_category("secrets", user_id=user_id) or {}
    except Exception:
        return False
    if not isinstance(secrets_cfg, dict):
        return False

    primary = (secrets_cfg.get("username") or "").strip()
    primary_pw = secrets_cfg.get("password")
    extras = secrets_cfg.get("linkedin_extra_accounts")
    has_canonical = bool(primary) or (
        isinstance(extras, list) and any(isinstance(r, dict) and r.get("username") for r in extras)
    )
    if not has_canonical:
        return False

    legacy = _legacy_linkedin_keys_from_secrets(secrets_cfg)
    next_idx = _next_linkedin_index(legacy)

    if primary and not legacy.get("LINKEDIN_USERNAME") and not _email_in_legacy(legacy, primary):
        db.set_config("LINKEDIN_USERNAME", primary, "secrets", user_id=user_id)
        if primary_pw is not None and str(primary_pw).strip():
            db.set_config("LINKEDIN_PASSWORD", str(primary_pw), "secrets", user_id=user_id)
        legacy = _legacy_linkedin_keys_from_secrets(
            db.get_all_by_category("secrets", user_id=user_id) or {}
        )
        next_idx = _next_linkedin_index(legacy)

    if isinstance(extras, list):
        for row in extras:
            if not isinstance(row, dict):
                continue
            u = (row.get("username") or "").strip()
            p = row.get("password")
            if not u or _email_in_legacy(legacy, u):
                continue
            db.set_config(
                f"LINKEDIN_USERNAME_{next_idx}", u, "secrets", user_id=user_id
            )
            if p is not None and str(p).strip():
                db.set_config(
                    f"LINKEDIN_PASSWORD_{next_idx}", str(p), "secrets", user_id=user_id
                )
            legacy[f"LINKEDIN_USERNAME_{next_idx}"] = u
            next_idx += 1

    for key in CANONICAL_LINKEDIN_KEYS:
        try:
            db.delete_config(key, "secrets", user_id=user_id)
        except Exception:
            pass

    logging.info("Migrated canonical LinkedIn secrets to LINKEDIN_* keys for %s", user_id)
    return True


def _iter_linkedin_key_accounts(keys: dict) -> list[tuple[str, str | None, bool]]:
    """Parse LINKEDIN_USERNAME / LINKEDIN_USERNAME_<n> map."""
    out: list[tuple[str, str | None, bool]] = []

    primary = keys.get("LINKEDIN_USERNAME")
    if isinstance(primary, str) and primary.strip():
        out.append((primary.strip(), keys.get("LINKEDIN_PASSWORD"), True))

    indexed: list[tuple[str, str, str | None]] = []
    prefix = "LINKEDIN_USERNAME_"
    for key, value in keys.items():
        if not key.startswith(prefix):
            continue
        suffix = key[len(prefix) :]
        if not suffix or not isinstance(value, str):
            continue
        u = value.strip()
        if not u:
            continue
        indexed.append((suffix, u, keys.get(f"LINKEDIN_PASSWORD_{suffix}")))

    def _suffix_sort_key(item: tuple[str, str, str | None]) -> tuple[int, object]:
        s = item[0]
        try:
            return (0, int(s))
        except ValueError:
            return (1, s)

    indexed.sort(key=_suffix_sort_key)
    for _, u, pw in indexed:
        out.append((u, pw, False))

    return out


def _ensure_primary_env_slots(env: dict, legacy: dict[str, str]) -> None:
    """Set LINKEDIN_USERNAME/PASSWORD from first account when only indexed keys exist."""
    if str(env.get("LINKEDIN_USERNAME") or "").strip():
        return
    accounts = _iter_linkedin_key_accounts(legacy)
    if not accounts:
        return
    username, password, _ = accounts[0]
    env["LINKEDIN_USERNAME"] = username
    if password is not None and str(password).strip():
        env["LINKEDIN_PASSWORD"] = str(password)


def apply_dashboard_linkedin_credentials(env: dict, *, user_id: str) -> None:
    """Inject LinkedIn credentials from DB into ``env`` for supervisor / bot subprocesses."""
    migrate_canonical_linkedin_to_legacy(user_id=user_id)
    try:
        secrets_cfg = db.get_all_by_category("secrets", user_id=user_id)
    except Exception:
        logging.warning("Could not read secrets from DB for LinkedIn credentials.")
        return
    legacy = _legacy_linkedin_keys_from_secrets(secrets_cfg or {})
    for key, value in legacy.items():
        if value:
            env[key] = value
    _ensure_primary_env_slots(env, legacy)


def preview_env_with_dashboard_credentials(*, user_id: str) -> dict:
    """DB-backed LinkedIn env snapshot (does not read ``.env``)."""
    env: dict = {}
    apply_dashboard_linkedin_credentials(env, user_id=user_id)
    return env


# ---------------------------------------------------------------------------
# Linkedln-Automation-Framework settings (DB category: linkedin_automation)
# ---------------------------------------------------------------------------

AUTOMATION_KEY_TO_ENV: dict[str, str] = {
    "openai_api_key": "OPENAI_API_KEY",
    "openai_model": "OPENAI_MODEL",
    "gemini_api_key": "GEMINI_API_KEY",
    "gemini_model": "GEMINI_MODEL",
    "use_gemini": "USE_GEMINI",
    "linkedin_ai_provider": "LINKEDIN_AI_PROVIDER",
    "grok_api_key": "GROK_API_KEY",
    "grok_model": "GROK_MODEL",
    "groq_api_key": "GROQ_API_KEY",
    "groq_model": "GROQ_MODEL",
    "headless": "HEADLESS",
    "marketing_mode": "MARKETING_MODE",
    "project_name": "PROJECT_NAME",
    "project_url": "PROJECT_URL",
    "project_pitch": "PROJECT_PITCH",
    "project_short_pitch": "PROJECT_SHORT_PITCH",
    "project_context": "PROJECT_CONTEXT",
    "project_tagline": "PROJECT_TAGLINE",
    "linkedin_resume_url": "LINKEDIN_RESUME_URL",
    "linkedin_github_username": "LINKEDIN_GITHUB_USERNAME",
    "linkedin_comment_display_name": "LINKEDIN_COMMENT_DISPLAY_NAME",
    "linkedin_comment_voice": "LINKEDIN_COMMENT_VOICE",
}

AUTOMATION_SENSITIVE_KEYS: set[str] = {
    "openai_api_key",
    "gemini_api_key",
    "grok_api_key",
    "groq_api_key",
}


def _coerce_env_value(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value).strip()
    return s or None


def apply_dashboard_automation_settings(env: dict, *, user_id: str) -> None:
    try:
        cfg = db.get_all_by_category("linkedin_automation", user_id=user_id)
    except Exception:
        logging.warning("Could not read linkedin_automation config from DB.")
        return
    if not isinstance(cfg, dict):
        return
    for db_key, env_key in AUTOMATION_KEY_TO_ENV.items():
        if db_key not in cfg:
            continue
        value = _coerce_env_value(cfg.get(db_key))
        if value is None or value == "":
            continue
        env[env_key] = value


def get_automation_settings(mask_sensitive: bool = True, *, user_id: str) -> dict:
    try:
        cfg = db.get_all_by_category("linkedin_automation", user_id=user_id)
    except Exception:
        cfg = {}
    if not isinstance(cfg, dict):
        cfg = {}
    out: dict = {}
    for db_key in AUTOMATION_KEY_TO_ENV:
        value = cfg.get(db_key)
        if mask_sensitive and db_key in AUTOMATION_SENSITIVE_KEYS:
            out[db_key] = "set" if value else ""
        else:
            out[db_key] = value
    return out


# ---------------------------------------------------------------------------
# Account discovery + selection
# ---------------------------------------------------------------------------


def _load_secrets(*, user_id: str) -> dict:
    migrate_canonical_linkedin_to_legacy(user_id=user_id)
    try:
        s = db.get_all_by_category("secrets", user_id=user_id) or {}
        return s if isinstance(s, dict) else {}
    except Exception:
        logging.warning("Could not read secrets from DB.")
        return {}


def get_linkedin_password_for_email(user_id: str, linkedin_email: str) -> str:
    """Resolve password from dashboard DB secrets only."""
    target = (linkedin_email or "").strip().lower()
    if not target:
        return ""
    secrets = _load_secrets(user_id=user_id)
    for username, password, _ in _iter_linkedin_key_accounts(
        _legacy_linkedin_keys_from_secrets(secrets)
    ):
        if username.lower() == target:
            return str(password or "")
    return ""


def list_supervisor_accounts(*, user_id: str) -> list[dict]:
    """LinkedIn accounts with passwords for the local job-applier supervisor."""
    secrets_cfg = _load_secrets(user_id=user_id)
    accounts: list[dict] = []
    seen: set[str] = set()

    def _add(account_id: str, username: str, password: str) -> None:
        u = username.strip()
        p = str(password or "").strip()
        if not u or not p:
            return
        key = u.lower()
        if key in seen:
            return
        seen.add(key)
        accounts.append({"id": account_id, "username": u, "password": p})

    legacy_keys = _legacy_linkedin_keys_from_secrets(secrets_cfg)
    for username, password, is_primary in _iter_linkedin_key_accounts(legacy_keys):
        if not password or not str(password).strip():
            continue
        account_id = "main"
        if not is_primary:
            account_id = "1"
            for env_key, env_val in legacy_keys.items():
                if (
                    env_key.startswith("LINKEDIN_USERNAME_")
                    and str(env_val).strip().lower() == username.lower()
                ):
                    account_id = env_key[len("LINKEDIN_USERNAME_") :]
                    break
        _add(account_id, username, str(password))

    for slot, account in enumerate(accounts, start=1):
        account["account_port"] = account_port_for_slot(slot)

    return accounts


def list_linkedin_accounts(*, user_id: str) -> list[dict]:
    """Configured LinkedIn accounts from DB (passwords not echoed)."""
    secrets_cfg = _load_secrets(user_id=user_id)
    out: list[dict] = []
    seen_lc: set[str] = set()
    has_primary = False

    legacy_keys = _legacy_linkedin_keys_from_secrets(secrets_cfg)
    for username, password, is_legacy_primary in _iter_linkedin_key_accounts(legacy_keys):
        if username.lower() in seen_lc:
            continue
        primary = is_legacy_primary and not has_primary
        out.append({
            "username": username,
            "primary": primary,
            "has_password": bool(password and str(password).strip()),
        })
        seen_lc.add(username.lower())
        if primary:
            has_primary = True

    return out


def count_linkedin_accounts(*, user_id: str) -> int:
    return len(list_linkedin_accounts(user_id=user_id))


def get_active_linkedin_account(
    env: dict | None = None, *, user_id: str | None = None
) -> str | None:
    if env is None:
        if not user_id:
            return None
        env = preview_env_with_dashboard_credentials(user_id=user_id)
    u = env.get("LINKEDIN_USERNAME")
    return u.strip() if isinstance(u, str) and u.strip() else None


def apply_linkedin_account(env: dict, account: str | None, *, user_id: str) -> str | None:
    if not account or not str(account).strip():
        return get_active_linkedin_account(env, user_id=user_id)

    needle = str(account).strip().lower()
    secrets_cfg = _load_secrets(user_id=user_id)
    legacy_keys = _legacy_linkedin_keys_from_secrets(secrets_cfg)

    for username, password, _ in _iter_linkedin_key_accounts(legacy_keys):
        if username.lower() != needle:
            continue
        env["LINKEDIN_USERNAME"] = username
        if password is not None and str(password).strip() != "":
            env["LINKEDIN_PASSWORD"] = str(password)
        return username

    return None
