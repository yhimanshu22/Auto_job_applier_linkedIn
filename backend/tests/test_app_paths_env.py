import os

from app_paths import persist_runtime_secrets_to_user_env


def test_persist_runtime_secrets_writes_missing_keys(tmp_path, monkeypatch):
    user_data = tmp_path / "LinkdApply"
    user_data.mkdir()
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(user_data))
    monkeypatch.setenv("ENCRYPTION_KEY", "test-key-abc")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")

    assert persist_runtime_secrets_to_user_env() is True

    env_text = (user_data / ".env").read_text(encoding="utf-8")
    assert "ENCRYPTION_KEY=test-key-abc" in env_text
    assert "LLM_API_KEY=sk-test" in env_text

    assert persist_runtime_secrets_to_user_env() is False


def test_persist_runtime_secrets_skips_when_user_data_unset(monkeypatch):
    monkeypatch.delenv("LINKDAPPLY_USER_DATA", raising=False)
    monkeypatch.setenv("ENCRYPTION_KEY", "test-key-abc")
    assert persist_runtime_secrets_to_user_env() is False
