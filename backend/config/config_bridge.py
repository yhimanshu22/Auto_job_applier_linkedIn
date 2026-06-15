import sys
import os

from dotenv import load_dotenv

# Bot subprocesses and early imports need env-backed secrets before DB is read.
load_dotenv()

# Ensure we can import db_manager from parent dir if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_manager import db


def _apply_config_normalizations(config_dict: dict) -> dict:
    """Migrate legacy settings (e.g. removed providers) before export to the bot."""
    if config_dict.get("ai_provider") == "openclaw":
        config_dict["ai_provider"] = "openai"
    return config_dict


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


def _load_bot_config() -> dict:
    user_id = _bot_user_id()
    config_dict = _base_config_defaults()

    for cat in ["personals", "search", "settings", "questions", "secrets"]:
        config_dict.update(db.get_all_by_category(cat, user_id=user_id))

    _apply_env_secret_fallbacks(config_dict)

    if os.getenv("LINKEDIN_USERNAME"):
        config_dict["username"] = os.getenv("LINKEDIN_USERNAME")
    if os.getenv("LINKEDIN_PASSWORD"):
        config_dict["password"] = os.getenv("LINKEDIN_PASSWORD")

    _apply_config_normalizations(config_dict)
    _apply_headless_server_defaults(config_dict)
    return config_dict


def load_config_to_module(module_name):
    config_dict = _load_bot_config()

    current_module = sys.modules[module_name]
    for k, v in config_dict.items():
        setattr(current_module, k, v)
    return config_dict

def _ensure_module_exports() -> dict:
    """Populate module-level config for ``from config.config_bridge import *``."""
    if os.getenv("USER_ID", "").strip():
        try:
            return _load_bot_config()
        except Exception:
            pass
    return _base_config_defaults()


# Initial load into this module so it can be imported with *
config_data = _ensure_module_exports()

# Export all keys to this module
for k, v in config_data.items():
    setattr(sys.modules[__name__], k, v)
