"""Enforce app-side LLM rate limits before cloud API calls."""

from __future__ import annotations

from . import config


def guard_llm_call(*, provider: str, api_key: str | None = None) -> None:
    try:
        from services.llm_rate_limit import LLMRateLimitExceeded, acquire_llm_call_slot
    except ImportError:
        return

    key = api_key
    if not key:
        if provider == "gemini":
            key = config.GEMINI_API_KEY
        elif provider == "openai":
            key = getattr(config, "OPENAI_API_KEY", None)
        elif provider == "grok":
            key = getattr(config, "GROK_API_KEY", None)
    try:
        acquire_llm_call_slot(provider=provider, api_key=key)
    except LLMRateLimitExceeded as exc:
        raise ValueError(str(exc)) from exc