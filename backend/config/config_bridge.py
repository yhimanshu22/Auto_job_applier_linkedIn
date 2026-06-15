import sys
import os

from app_paths import get_runtime_writable_root, load_env_files

# Bot subprocesses and early imports need env-backed secrets before DB is read.
load_env_files()

# Ensure we can import db_manager from parent dir if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_manager import db
from services.linkedin_env import (
    _iter_linkedin_key_accounts,
    _legacy_linkedin_keys_from_secrets,
    migrate_canonical_linkedin_to_legacy,
)


def _apply_config_normalizations(config_dict: dict) -> dict:
    """Migrate legacy settings (e.g. removed providers) before export to the bot."""
    if config_dict.get("ai_provider") == "openclaw":
        config_dict["ai_provider"] = "openai"
    _coerce_config_types(config_dict)
    return config_dict


_INT_CONFIG_KEYS = (
    "desired_salary",
    "notice_period",
    "current_ctc",
    "switch_number",
    "current_experience",
    "click_gap",
    "bot_speed",
    "daily_apply_limit",
    "max_applications_per_day",
    "rate_limit_delay_min_sec",
    "rate_limit_delay_max_sec",
    "rate_limit_daily_jitter",
)


def _coerce_config_types(config_dict: dict) -> None:
    """SQLite/JSON often yields floats (e.g. -1.0); validator expects strict ints."""
    for key in _INT_CONFIG_KEYS:
        if key not in config_dict:
            continue
        val = config_dict[key]
        if isinstance(val, bool):
            continue
        if isinstance(val, int):
            continue
        if isinstance(val, float) and val == int(val):
            config_dict[key] = int(val)
        elif isinstance(val, str) and val.strip().lstrip("-").isdigit():
            config_dict[key] = int(val.strip())


def _apply_headless_server_defaults(config_dict: dict) -> dict:
    """Servers without a display must run Chrome headless or the bot cannot start."""
    if os.name == "nt":
        return config_dict
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return config_dict
    if not config_dict.get("run_in_background"):
        config_dict["run_in_background"] = True
    return config_dict


def _bot_user_id() -> str:
    """The bot subprocess is launched with USER_ID in its env (see routes/bot.py)."""
    uid = os.getenv("USER_ID", "").strip()
    if not uid:
        raise RuntimeError("USER_ID environment variable is required")
    return uid


def _base_config_defaults() -> dict:
    return {
        "file_name": "all excels/all_applied_applications_history.csv",
        "failed_file_name": "all excels/all_failed_applications_history.csv",
        "logs_folder_path": "logs/",
        "generated_resume_path": "all resumes/generated",
        "default_resume_path": "all resumes/default_resume.pdf",
        "daily_apply_limit": 50,
        "smart_rate_limiting": True,
        "max_applications_per_day": 40,
        "rate_limit_delay_min_sec": 12,
        "rate_limit_delay_max_sec": 44,
        "rate_limit_daily_jitter": 12,
        "run_in_background": False,
        "use_AI": True,
        "stream_output": True,
        "showAiErrorAlerts": False,
        "ai_provider": "openai",
        "llm_api_url": "https://api.groq.com/openai/v1/",
        "llm_model": "llama-3.3-70b-versatile",
        "llm_spec": "openai",
        "llm_api_key": "",
        # settings.py — required by open_chrome / validator when DB rows are missing
        "close_tabs": True,
        "follow_companies": False,
        "run_non_stop": False,
        "alternate_sortby": False,
        "cycle_date_posted": False,
        "stop_date_cycle_at_24hr": False,
        "click_gap": 0,
        "bot_speed": 5,
        "disable_extensions": False,
        "safe_mode": False,
        "smooth_scroll": True,
        "keep_screen_awake": False,
        "stealth_mode": False,
        # personals.py — run_ai_bot.state imports these before validate_config()
        "first_name": "",
        "middle_name": "",
        "last_name": "",
        "phone_number": "",
        "current_city": "",
        "street": "",
        "state": "",
        "zipcode": "",
        "country": "",
        "ethnicity": "Decline",
        "gender": "",
        "disability_status": "Decline",
        "veteran_status": "Decline",
        # questions.py
        "years_of_experience": "0",
        "require_visa": "No",
        "website": "",
        "linkedIn": "",
        "desired_salary": 0,
        "us_citizenship": "Other",
        "linkedin_headline": "",
        "notice_period": 0,
        "current_ctc": 0,
        "linkedin_summary": "",
        "cover_letter": "",
        "recent_employer": "",
        "confidence_level": "",
        "pause_before_submit": False,
        "pause_at_failed_question": False,
        "overwrite_previous_answers": False,
        # search.py — lists must exist even when empty
        "search_terms": [],
        "search_location": "",
        "switch_number": 1,
        "randomize_search_order": False,
        "sort_by": "",
        "date_posted": "",
        "salary": "",
        "easy_apply_only": False,
        "experience_level": [],
        "job_type": [],
        "on_site": [],
        "companies": [],
        "location": [],
        "industry": [],
        "job_function": [],
        "job_titles": [],
        "benefits": [],
        "commitments": [],
        "under_10_applicants": False,
        "in_your_network": False,
        "fair_chance_employer": False,
        "pause_after_filters": False,
        "about_company_bad_words": [],
        "about_company_good_words": [],
        "bad_words": [],
        "security_clearance": False,
        "did_masters": False,
        "current_experience": -1,
    }


def _apply_env_secret_fallbacks(config_dict: dict) -> None:
    """Use backend/.env LLM_* vars when the dashboard DB has no key yet."""
    env_map = {
        "llm_api_key": "LLM_API_KEY",
        "llm_api_url": "LLM_API_URL",
        "llm_model": "LLM_MODEL",
        "llm_spec": "LLM_SPEC",
        "ai_provider": "AI_PROVIDER",
    }
    for config_key, env_key in env_map.items():
        if config_dict.get(config_key) in (None, ""):
            env_val = (os.getenv(env_key) or "").strip()
            if env_val:
                config_dict[config_key] = env_val


def _apply_linkedin_db_to_bot_credentials(config_dict: dict) -> None:
    """Map LINKEDIN_USERNAME* DB keys to username/password for validate_secrets."""
    if config_dict.get("username") and config_dict.get("password"):
        return
    legacy = _legacy_linkedin_keys_from_secrets(config_dict)
    accounts = _iter_linkedin_key_accounts(legacy)
    if not accounts:
        return
    username, password, _ = accounts[0]
    if not config_dict.get("username"):
        config_dict["username"] = username
    if not config_dict.get("password") and password:
        config_dict["password"] = password


def _resolve_default_resume_path(config_dict: dict, user_id: str) -> None:
    """Map dashboard uploads (filename or DB metadata) to a path the bot can open."""
    try:
        resumes = db.get_user_resumes(user_id)
        default = next((r for r in resumes if r.get("is_default")), None)
        if not default and resumes:
            default = resumes[0]
        if default:
            storage_path = (default.get("storage_path") or "").strip()
            if storage_path and os.path.isfile(storage_path):
                config_dict["default_resume_path"] = storage_path
                return
    except Exception:
        pass

    path = (config_dict.get("default_resume_path") or "").strip()
    if not path:
        return
    if os.path.isfile(path):
        return

    root = get_runtime_writable_root()
    if not os.path.dirname(path):
        candidate = os.path.join(root, "all resumes", user_id, path)
        if os.path.isfile(candidate):
            config_dict["default_resume_path"] = candidate


def fetch_bot_config_from_db() -> dict:
    """Read bot configuration from SQLite (single load; use cache during job runs)."""
    user_id = _bot_user_id()
    migrate_canonical_linkedin_to_legacy(user_id=user_id)
    config_dict = _base_config_defaults()

    for cat in ["personals", "search", "settings", "questions", "secrets"]:
        config_dict.update(db.get_all_by_category(cat, user_id=user_id))

    _apply_env_secret_fallbacks(config_dict)
    _apply_linkedin_db_to_bot_credentials(config_dict)

    _apply_config_normalizations(config_dict)
    _apply_headless_server_defaults(config_dict)
    _resolve_default_resume_path(config_dict, user_id)

    # Supervisor-spawned workers inject per-account LINKEDIN_* into this process env.
    # Do not read credentials from backend/.env — only from that injection.
    if os.getenv("BOT_ID"):
        injected_user = os.getenv("LINKEDIN_USERNAME")
        injected_pass = os.getenv("LINKEDIN_PASSWORD")
        if injected_user and str(injected_user).strip():
            config_dict["username"] = str(injected_user).strip()
        if injected_pass is not None and str(injected_pass).strip() != "":
            config_dict["password"] = str(injected_pass)

    return config_dict


def _load_bot_config() -> dict:
    """Fresh DB read (tests, explicit reload). Prefer ``warm_bot_config_cache()`` in bots."""
    return fetch_bot_config_from_db()


def load_config_to_module(module_name):
    from services.bot_config_cache import warm_bot_config_cache

    config_dict = warm_bot_config_cache()

    current_module = sys.modules[module_name]
    for k, v in config_dict.items():
        setattr(current_module, k, v)
    return config_dict

def _ensure_module_exports() -> dict:
    """Populate module-level config for ``from config.config_bridge import *``."""
    if os.getenv("USER_ID", "").strip():
        try:
            from services.bot_config_cache import warm_bot_config_cache

            return warm_bot_config_cache()
        except Exception:
            pass
    return _base_config_defaults()


# Initial load into this module so it can be imported with *
config_data = _ensure_module_exports()

# Export all keys to this module
for k, v in config_data.items():
    setattr(sys.modules[__name__], k, v)
