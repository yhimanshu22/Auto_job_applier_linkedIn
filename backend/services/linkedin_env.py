"""LinkedIn account discovery from DB secrets (aligned with supervisor.BotSupervisor._get_accounts).

Also exposes Linkedln-Automation-Framework settings injection so dashboard-managed
AI keys, marketing mode, and project metadata are passed into the framework
subprocess at launch time.
"""

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


# ---------------------------------------------------------------------------
# Linkedln-Automation-Framework settings (DB category: linkedin_automation)
# ---------------------------------------------------------------------------

# Maps the DB key (snake_case, dashboard form) -> env var the framework reads.
AUTOMATION_KEY_TO_ENV: dict[str, str] = {
    "openai_api_key": "OPENAI_API_KEY",
    "openai_model": "OPENAI_MODEL",
    "gemini_api_key": "GEMINI_API_KEY",
    "use_gemini": "USE_GEMINI",
    "headless": "HEADLESS",
    "marketing_mode": "MARKETING_MODE",
    "project_name": "PROJECT_NAME",
    "project_url": "PROJECT_URL",
    "project_pitch": "PROJECT_PITCH",
    "project_short_pitch": "PROJECT_SHORT_PITCH",
    "project_context": "PROJECT_CONTEXT",
    "project_tagline": "PROJECT_TAGLINE",
}

AUTOMATION_SENSITIVE_KEYS: set[str] = {"openai_api_key", "gemini_api_key"}


def _coerce_env_value(value) -> str | None:
    """Convert dashboard-stored JSON value to the string the framework expects."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value).strip()
    return s or None


def apply_dashboard_automation_settings(env: dict) -> None:
    """Inject framework env vars from the dashboard DB (category 'linkedin_automation').

    Only sets keys that are configured and non-empty; existing env values win
    when no dashboard override has been saved.
    """
    try:
        cfg = db.get_all_by_category("linkedin_automation")
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


def get_automation_settings(mask_sensitive: bool = True) -> dict:
    """Return the dashboard-configured automation settings.

    Sensitive values (API keys) are reduced to ``"set"`` / ``""`` when
    ``mask_sensitive=True`` so we don't expose raw keys in HTTP responses.
    """
    try:
        cfg = db.get_all_by_category("linkedin_automation")
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


# ---------------------------------------------------------------------------
# Account discovery + selection (used by the automation dashboard)
# ---------------------------------------------------------------------------


def _load_secrets() -> dict:
    try:
        s = db.get_all_by_category("secrets") or {}
        return s if isinstance(s, dict) else {}
    except Exception:
        logging.warning("Could not read secrets from DB.")
        return {}


def _iter_env_accounts(env: dict) -> list[tuple[str, str | None, bool]]:
    """Pull LinkedIn accounts that live in environment variables.

    Returns ``(username, password, is_primary)`` tuples. ``LINKEDIN_USERNAME``
    is treated as primary; ``LINKEDIN_USERNAME_<suffix>`` entries follow in
    numeric-suffix order (falling back to lexicographic for non-numeric
    suffixes).
    """
    out: list[tuple[str, str | None, bool]] = []

    primary = env.get("LINKEDIN_USERNAME")
    if isinstance(primary, str) and primary.strip():
        out.append((primary.strip(), env.get("LINKEDIN_PASSWORD"), True))

    indexed: list[tuple[str, str, str | None]] = []
    prefix = "LINKEDIN_USERNAME_"
    for key, value in env.items():
        if not key.startswith(prefix):
            continue
        suffix = key[len(prefix):]
        if not suffix or not isinstance(value, str):
            continue
        u = value.strip()
        if not u:
            continue
        indexed.append((suffix, u, env.get(f"LINKEDIN_PASSWORD_{suffix}")))

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


def list_linkedin_accounts(env: dict | None = None) -> list[dict]:
    """Return all configured LinkedIn accounts from BOTH the DB ``secrets``
    category and the process environment (``LINKEDIN_USERNAME`` /
    ``LINKEDIN_USERNAME_<n>`` style variables loaded from ``.env``).

    Passwords are never echoed. Each entry has the shape
    ``{"username": str, "primary": bool, "has_password": bool}``.
    Ordering: DB primary first, then DB extras in stored order, then any
    env-only accounts in suffix order. Duplicates (case-insensitive) are
    collapsed to a single entry preferring the DB-side metadata.
    """
    if env is None:
        env = preview_env_with_dashboard_credentials()

    secrets_cfg = _load_secrets()
    out: list[dict] = []
    seen_lc: set[str] = set()

    primary = (secrets_cfg.get("username") or "").strip()
    primary_pw = secrets_cfg.get("password")
    if primary:
        out.append({
            "username": primary,
            "primary": True,
            "has_password": bool(primary_pw and str(primary_pw).strip()),
        })
        seen_lc.add(primary.lower())

    extras = secrets_cfg.get("linkedin_extra_accounts")
    if isinstance(extras, list):
        for row in extras:
            if not isinstance(row, dict):
                continue
            u = (row.get("username") or "").strip()
            if not u or u.lower() in seen_lc:
                continue
            out.append({
                "username": u,
                "primary": False,
                "has_password": bool(row.get("password")),
            })
            seen_lc.add(u.lower())

    db_primary_set = any(r["primary"] for r in out)
    for username, password, is_env_primary in _iter_env_accounts(env):
        if username.lower() in seen_lc:
            continue
        out.append({
            "username": username,
            "primary": is_env_primary and not db_primary_set,
            "has_password": bool(password and str(password).strip()),
        })
        seen_lc.add(username.lower())
        if is_env_primary:
            db_primary_set = True
    return out


def get_active_linkedin_account(env: dict | None = None) -> str | None:
    """Resolve which username a subprocess will authenticate as.

    Reads ``LINKEDIN_USERNAME`` from the supplied env (or a snapshot of the
    dashboard-augmented env). Returns ``None`` when nothing is configured.
    """
    if env is None:
        env = preview_env_with_dashboard_credentials()
    u = env.get("LINKEDIN_USERNAME")
    return u.strip() if isinstance(u, str) and u.strip() else None


def apply_linkedin_account(env: dict, account: str | None) -> str | None:
    """Override ``LINKEDIN_USERNAME`` / ``LINKEDIN_PASSWORD`` in ``env`` with the
    chosen account's credentials.

    Lookup is case-insensitive across the primary username and the extras
    list. When ``account`` is falsy, the env stays untouched and the primary
    account is used.

    Returns the resolved username (or ``None`` when ``account`` was given but
    no match was found — in that case env stays untouched and the caller can
    surface the error).
    """
    # Default behaviour: keep whatever ``apply_dashboard_linkedin_credentials``
    # already wrote (primary). Just return whoever's currently configured.
    if not account or not str(account).strip():
        return get_active_linkedin_account(env)

    needle = str(account).strip().lower()
    secrets_cfg = _load_secrets()

    primary = (secrets_cfg.get("username") or "").strip()
    if primary and primary.lower() == needle:
        env["LINKEDIN_USERNAME"] = primary
        pw = secrets_cfg.get("password")
        if pw is not None and str(pw).strip() != "":
            env["LINKEDIN_PASSWORD"] = str(pw)
        return primary

    extras = secrets_cfg.get("linkedin_extra_accounts")
    if isinstance(extras, list):
        for row in extras:
            if not isinstance(row, dict):
                continue
            u = (row.get("username") or "").strip()
            if u and u.lower() == needle:
                env["LINKEDIN_USERNAME"] = u
                pw = row.get("password")
                if pw is not None and str(pw).strip() != "":
                    env["LINKEDIN_PASSWORD"] = str(pw)
                return u

    # Fallback: env-only accounts loaded from .env (LINKEDIN_USERNAME_<n>).
    for username, password, _is_primary in _iter_env_accounts(env):
        if username.lower() != needle:
            continue
        env["LINKEDIN_USERNAME"] = username
        if password is not None and str(password).strip() != "":
            env["LINKEDIN_PASSWORD"] = str(password)
        return username

    return None
