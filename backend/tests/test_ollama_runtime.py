"""Tests for local Ollama model selection."""

from linkedin_automation.ollama_runtime import pick_smallest_model


def test_pick_smallest_model_by_size():
    models = [
        {"name": "qwen2.5:7b", "size": 4_683_087_332},
        {"name": "qwen2.5:1.5b", "size": 986_061_892},
        {"name": "x_bot_finetuned:latest", "size": 4_683_099_216},
    ]
    assert pick_smallest_model(models) == "qwen2.5:1.5b"


def test_pick_smallest_model_empty():
    assert pick_smallest_model([]) is None


def test_resolve_provider_explicit_ollama(monkeypatch):
    from linkedin_automation import config

    monkeypatch.setattr(config, "LINKEDIN_AI_PROVIDER", "ollama")
    assert config.resolve_linkedin_ai_provider() == "ollama"


def test_resolve_provider_autopick_ollama(monkeypatch):
    from linkedin_automation import config

    monkeypatch.setattr(config, "LINKEDIN_AI_PROVIDER", "")
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)
    monkeypatch.setattr(config, "GROK_API_KEY", None)
    monkeypatch.setattr(
        "linkedin_automation.ollama_runtime.ollama_available", lambda *a, **k: True
    )
    assert config.resolve_linkedin_ai_provider() == "ollama"