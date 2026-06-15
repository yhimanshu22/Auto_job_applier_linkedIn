import os

import pytest

from config import config_bridge
from services.bot_config_cache import (
    clear_bot_config_cache,
    get_cached_user_resumes,
    get_rate_settings,
    warm_bot_config_cache,
)


def test_warm_bot_config_cache_loads_once(monkeypatch, test_db):
    uid = "cache-user@test.com"
    monkeypatch.setenv("USER_ID", uid)
    clear_bot_config_cache()
    test_db.set_config("bot_speed", 7, "settings", user_id=uid)
    test_db.set_config("LINKEDIN_USERNAME", "u@example.com", "secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD", "pw", "secrets", user_id=uid)

    cfg1 = warm_bot_config_cache()
    cfg2 = warm_bot_config_cache()

    assert cfg1 is cfg2
    assert cfg1["bot_speed"] == 7
    assert get_rate_settings().max_applications_per_day == 40


def test_warm_prefetches_resumes(monkeypatch, test_db):
    uid = "cache-resume@test.com"
    monkeypatch.setenv("USER_ID", uid)
    clear_bot_config_cache()
    path = os.path.join(os.getcwd(), "all resumes", uid, "cv.pdf")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(b"%PDF")
    test_db.upsert_resume_metadata(uid, "cv.pdf", path, is_default=True)
    test_db.set_config("LINKEDIN_USERNAME", "u@example.com", "secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD", "pw", "secrets", user_id=uid)

    warm_bot_config_cache()
    resumes = get_cached_user_resumes()

    assert len(resumes) == 1
    assert resumes[0]["file_name"] == "cv.pdf"


def test_load_rate_settings_uses_cache_when_warmed(monkeypatch, test_db):
    from services.smart_rate_limit import load_rate_settings_from_db

    uid = "cache-rate@test.com"
    monkeypatch.setenv("USER_ID", uid)
    clear_bot_config_cache()
    test_db.set_config("max_applications_per_day", 33, "settings", user_id=uid)
    test_db.set_config("LINKEDIN_USERNAME", "u@example.com", "secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD", "pw", "secrets", user_id=uid)

    warm_bot_config_cache()
    settings = load_rate_settings_from_db(user_id=uid)

    assert settings.max_applications_per_day == 33
