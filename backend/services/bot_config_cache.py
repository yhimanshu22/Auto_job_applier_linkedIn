"""In-memory configuration snapshot for a bot worker process.

Load once at startup; job execution reads from memory instead of SQLite.
"""

from __future__ import annotations

import os
from typing import Any

from services.smart_rate_limit import RateLimitSettings, settings_from_mapping

_config: dict[str, Any] | None = None
_rate_settings: RateLimitSettings | None = None
_user_resumes: list[dict] | None = None
_default_resume_asset: dict | None = None
_warmed: bool = False


def is_warmed() -> bool:
    return _warmed


def clear_bot_config_cache() -> None:
    """Drop cached config (tests and forced reload)."""
    global _config, _rate_settings, _user_resumes, _default_resume_asset, _warmed
    _config = None
    _rate_settings = None
    _user_resumes = None
    _default_resume_asset = None
    _warmed = False


def warm_bot_config_cache(*, force: bool = False) -> dict[str, Any]:
    """Load dashboard config + resume metadata from DB once into memory."""
    global _config, _rate_settings, _user_resumes, _default_resume_asset, _warmed
    if _warmed and not force:
        return _config  # type: ignore[return-value]

    from config.config_bridge import fetch_bot_config_from_db

    config = fetch_bot_config_from_db()
    user_id = os.getenv("USER_ID", "").strip()

    resumes: list[dict] = []
    default_asset = None
    if user_id:
        from db_manager import db

        try:
            resumes = list(db.get_user_resumes(user_id) or [])
        except Exception:
            resumes = []
        try:
            default_asset = db.get_asset("default_resume")
        except Exception:
            default_asset = None

    _config = config
    _rate_settings = settings_from_mapping(config)
    _user_resumes = resumes
    _default_resume_asset = default_asset
    _warmed = True
    return config


def get_bot_config() -> dict[str, Any]:
    if not _warmed:
        return warm_bot_config_cache()
    return _config  # type: ignore[return-value]


def get_rate_settings_if_warmed() -> RateLimitSettings | None:
    if not _warmed:
        return None
    return _rate_settings


def get_rate_settings() -> RateLimitSettings:
    if not _warmed:
        warm_bot_config_cache()
    return _rate_settings  # type: ignore[return-value]


def get_cached_user_resumes() -> list[dict]:
    if not _warmed:
        warm_bot_config_cache()
    return list(_user_resumes or [])


def get_cached_default_resume_asset() -> dict | None:
    if not _warmed:
        warm_bot_config_cache()
    return _default_resume_asset
