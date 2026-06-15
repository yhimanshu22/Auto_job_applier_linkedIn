import os

import pytest

from config import config_bridge


def test_load_bot_config_includes_chrome_settings(monkeypatch, test_db):
    uid = "bot-config-user@test.com"
    monkeypatch.setenv("USER_ID", uid)
    test_db.set_config("LINKEDIN_USERNAME", "user@example.com", "secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD", "secret123", "secrets", user_id=uid)

    cfg = config_bridge._load_bot_config()

    assert cfg["generated_resume_path"] == "all resumes/generated"
    assert cfg["default_resume_path"] == "all resumes/default_resume.pdf"
    assert cfg["stealth_mode"] is False
    assert cfg["safe_mode"] is False
    assert cfg["username"] == "user@example.com"
    assert cfg["password"] == "secret123"


def test_load_bot_config_includes_personals_defaults(monkeypatch, test_db):
    uid = "bot-config-user@test.com"
    monkeypatch.setenv("USER_ID", uid)

    cfg = config_bridge._load_bot_config()

    assert cfg["middle_name"] == ""
    assert cfg["first_name"] == ""
    assert cfg["desired_salary"] == 0
    assert cfg["search_terms"] == []


def test_load_bot_config_requires_user_id(monkeypatch):
    monkeypatch.delenv("USER_ID", raising=False)
    with pytest.raises(RuntimeError, match="USER_ID"):
        config_bridge._load_bot_config()


def test_bot_worker_uses_injected_linkedin_env(monkeypatch, test_db):
    uid = "bot-config-user@test.com"
    monkeypatch.setenv("USER_ID", uid)
    monkeypatch.setenv("BOT_ID", "1")
    monkeypatch.setenv("LINKEDIN_USERNAME", "worker@example.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD", "worker-secret")
    test_db.set_config("LINKEDIN_USERNAME", "db-primary@example.com", "secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD", "db-secret", "secrets", user_id=uid)

    cfg = config_bridge._load_bot_config()

    assert cfg["username"] == "worker@example.com"
    assert cfg["password"] == "worker-secret"
