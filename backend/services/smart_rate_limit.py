"""Per-account daily caps and randomized delays for job-applier bots."""

from __future__ import annotations

import hashlib
import os
import random
import time
from dataclasses import dataclass
from datetime import date
from typing import Callable


@dataclass(frozen=True)
class RateLimitSettings:
    smart_rate_limiting: bool = True
    max_applications_per_day: int = 40
    rate_limit_delay_min_sec: int = 12
    rate_limit_delay_max_sec: int = 44
    rate_limit_daily_jitter: int = 12
    daily_apply_limit: int = 50  # legacy fallback when smart limiting is off


def _coerce_int(val, default: int) -> int:
    if isinstance(val, bool):
        return default
    if isinstance(val, int):
        return val
    if isinstance(val, float) and val == int(val):
        return int(val)
    if isinstance(val, str) and val.strip().lstrip("-").isdigit():
        return int(val.strip())
    return default


def settings_from_mapping(cfg: dict | None) -> RateLimitSettings:
    cfg = cfg or {}
    base = _coerce_int(cfg.get("max_applications_per_day"), 40)
    delay_min = _coerce_int(cfg.get("rate_limit_delay_min_sec"), 12)
    delay_max = _coerce_int(cfg.get("rate_limit_delay_max_sec"), 44)
    if delay_max < delay_min:
        delay_min, delay_max = delay_max, delay_min
    return RateLimitSettings(
        smart_rate_limiting=bool(cfg.get("smart_rate_limiting", True)),
        max_applications_per_day=max(1, base),
        rate_limit_delay_min_sec=max(1, delay_min),
        rate_limit_delay_max_sec=max(1, delay_max),
        rate_limit_daily_jitter=max(0, _coerce_int(cfg.get("rate_limit_daily_jitter"), 12)),
        daily_apply_limit=max(1, _coerce_int(cfg.get("daily_apply_limit"), 50)),
    )


def load_rate_settings_from_db(*, user_id: str) -> RateLimitSettings:
    from services.bot_config_cache import get_rate_settings_if_warmed

    cached = get_rate_settings_if_warmed()
    if cached is not None:
        return cached

    from db_manager import db

    cfg = db.get_all_by_category("settings", user_id=user_id)
    return settings_from_mapping(cfg)


def account_daily_application_limit(
    *,
    user_id: str,
    bot_id: str,
    base: int = 40,
    jitter: int = 12,
    on_date: date | None = None,
) -> int:
    """
    Stable per-account daily cap with small random offset (same value all day).

    Example with base=40, jitter=12: account 1 -> 43, account 2 -> 37, etc.
    """
    on_date = on_date or date.today()
    tag = f"{user_id}|{bot_id}|{on_date.isoformat()}|{base}|{jitter}"
    digest = hashlib.sha256(tag.encode("utf-8")).hexdigest()
    span = 2 * jitter + 1
    offset = (int(digest[:8], 16) % span) - jitter
    return max(1, base + offset)


def random_delay_seconds(settings: RateLimitSettings) -> float:
    return random.uniform(
        float(settings.rate_limit_delay_min_sec),
        float(settings.rate_limit_delay_max_sec),
    )


def effective_daily_limit(
    settings: RateLimitSettings,
    *,
    user_id: str,
    bot_id: str | None = None,
) -> int:
    if not settings.smart_rate_limiting:
        return settings.daily_apply_limit
    bid = (bot_id or os.getenv("BOT_ID") or os.getenv("LINKEDIN_USERNAME") or "default").strip()
    return account_daily_application_limit(
        user_id=user_id,
        bot_id=bid,
        base=settings.max_applications_per_day,
        jitter=settings.rate_limit_daily_jitter,
    )


def sleep_random_delay(
    settings: RateLimitSettings,
    *,
    reason: str,
    log: Callable[[str], None] | None = None,
) -> float:
    delay = random_delay_seconds(settings)
    if log:
        log(f"Smart rate limit: {reason} — pausing {delay:.1f}s")
    time.sleep(delay)
    return delay


def supervisor_stagger_sleep(settings: RateLimitSettings) -> float:
    if not settings.smart_rate_limiting:
        return 15.0
    return random_delay_seconds(settings)
