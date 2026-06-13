import sys
import os

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
    return os.getenv("USER_ID", "").strip() or "local-user"


def _base_config_defaults() -> dict:
    return {
        "file_name": "all excels/all_applied_applications_history.csv",
        "failed_file_name": "all excels/all_failed_applications_history.csv",
        "logs_folder_path": "logs/",
        "daily_apply_limit": 50,
        "run_in_background": False,
        "use_AI": True,
        "stream_output": True,
        "showAiErrorAlerts": False,
        "ai_provider": "openai",
        "llm_api_url": "https://api.groq.com/openai/v1/",
        "llm_model": "llama-3.3-70b-versatile",
        "llm_spec": "openai",
    }


def _fill_missing_secrets_from_template(config_dict: dict, user_id: str) -> None:
    """New dashboard users inherit search/settings but not secrets — copy AI keys only."""
    if user_id == "local-user":
        return
    template = db.get_all_by_category("secrets", user_id="local-user")
    if not isinstance(template, dict):
        return
    for key in (
        "stream_output",
        "showAiErrorAlerts",
        "use_AI",
        "ai_provider",
        "llm_api_url",
        "llm_model",
        "llm_spec",
        "llm_api_key",
    ):
        if config_dict.get(key) in (None, ""):
            if key in template and template[key] not in (None, ""):
                config_dict[key] = template[key]


def _load_bot_config() -> dict:
    user_id = _bot_user_id()
    config_dict = _base_config_defaults()

    for cat in ["personals", "search", "settings", "questions", "secrets"]:
        config_dict.update(db.get_all_by_category(cat, user_id=user_id))

    _fill_missing_secrets_from_template(config_dict, user_id)

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

# Initial load into this module so it can be imported with *
config_data = _load_bot_config()

# Export all keys to this module
for k, v in config_data.items():
    setattr(sys.modules[__name__], k, v)
