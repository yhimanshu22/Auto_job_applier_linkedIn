"""Tests for per-user / per-key LLM rate limits."""

import os

import pytest

from services.llm_rate_limit import (
    LLMRateLimitExceeded,
    acquire_llm_call_slot,
    settings_from_env,
)


@pytest.fixture
def rate_db(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    monkeypatch.setenv("LLM_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("LLM_MAX_CALLS_PER_MINUTE", "2")
    monkeypatch.setenv("LLM_MAX_CALLS_PER_HOUR", "100")
    monkeypatch.setenv("LLM_MAX_CALLS_PER_DAY", "100")
    monkeypatch.setenv("LLM_MAX_KEY_CALLS_PER_MINUTE", "3")
    monkeypatch.setenv("LLM_MAX_KEY_CALLS_PER_HOUR", "100")
    monkeypatch.setenv("LLM_MAX_KEY_CALLS_PER_DAY", "100")
    yield tmp_path


def test_acquire_respects_per_user_minute_cap(rate_db, monkeypatch):
    monkeypatch.setenv("USER_ID", "alice@test.com")
    acquire_llm_call_slot(provider="gemini", api_key="AIza-test-key-1")
    acquire_llm_call_slot(provider="gemini", api_key="AIza-test-key-1")
    with pytest.raises(LLMRateLimitExceeded, match="user cap"):
        acquire_llm_call_slot(provider="gemini", api_key="AIza-test-key-1")


def test_key_cap_shared_across_users(rate_db, monkeypatch):
    key = "AIza-shared-secret"
    monkeypatch.setenv("USER_ID", "u1@test.com")
    acquire_llm_call_slot(provider="gemini", api_key=key)
    monkeypatch.setenv("USER_ID", "u2@test.com")
    acquire_llm_call_slot(provider="gemini", api_key=key)
    monkeypatch.setenv("USER_ID", "u3@test.com")
    acquire_llm_call_slot(provider="gemini", api_key=key)
    monkeypatch.setenv("USER_ID", "u4@test.com")
    with pytest.raises(LLMRateLimitExceeded, match="API key cap"):
        acquire_llm_call_slot(provider="gemini", api_key=key)


def test_disabled_via_env(monkeypatch):
    monkeypatch.setenv("LLM_RATE_LIMIT_ENABLED", "false")
    assert settings_from_env().enabled is False
    for _ in range(20):
        acquire_llm_call_slot(provider="gemini", api_key="k")


def test_apply_dashboard_llm_rate_env(test_db, monkeypatch):
    uid = "automation-test@example.com"
    test_db.set_config("llm_rate_limit_enabled", True, "linkedin_automation", user_id=uid)
    test_db.set_config("llm_max_calls_per_day", 99, "linkedin_automation", user_id=uid)
    test_db.set_config("llm_max_key_calls_per_day", 150, "linkedin_automation", user_id=uid)
    from services.linkedin_env import apply_dashboard_automation_settings

    env: dict = {}
    apply_dashboard_automation_settings(env, user_id=uid)
    assert env["LLM_RATE_LIMIT_ENABLED"] == "true"
    assert env["LLM_MAX_CALLS_PER_DAY"] == "99"
    assert env["LLM_MAX_KEY_CALLS_PER_DAY"] == "150"