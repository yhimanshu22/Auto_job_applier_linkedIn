"""Job-applier bot: LLM rate limit guard (shared with LinkedIn automation)."""

from __future__ import annotations

import os


def guard_llm_call(*, provider: str, api_key: str | None = None) -> None:
    try:
        from services.llm_rate_limit import LLMRateLimitExceeded, acquire_llm_call_slot
    except ImportError:
        return

    key = api_key
    if not key:
        try:
            from config.config_bridge import llm_api_key

            key = llm_api_key
        except Exception:
            key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
    try:
        acquire_llm_call_slot(provider=provider, api_key=key)
    except LLMRateLimitExceeded as exc:
        raise ValueError(str(exc)) from exc