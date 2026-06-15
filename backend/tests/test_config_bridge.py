import os

import pytest

from config import config_bridge


def test_load_bot_config_includes_chrome_settings(monkeypatch, test_db):
    uid = "bot-config-user@test.com"
    monkeypatch.setenv("USER_ID", uid)
    monkeypatch.setenv("LINKEDIN_USERNAME", "user@example.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD", "secret123")

    cfg = config_bridge._load_bot_config()

    assert cfg["generated_resume_path"] == "all resumes/generated"
    assert cfg["default_resume_path"] == "all resumes/default_resume.pdf"
    assert cfg["stealth_mode"] is False
    assert cfg["safe_mode"] is False
    assert cfg["username"] == "user@example.com"
    assert cfg["password"] == "secret123"


def test_load_bot_config_requires_user_id(monkeypatch):
    monkeypatch.delenv("USER_ID", raising=False)
    with pytest.raises(RuntimeError, match="USER_ID"):
        config_bridge._load_bot_config()
