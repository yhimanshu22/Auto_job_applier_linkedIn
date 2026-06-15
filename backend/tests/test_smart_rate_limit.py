"""Tests for per-account smart rate limiting."""

from datetime import date

from services.smart_rate_limit import (
    account_daily_application_limit,
    effective_daily_limit,
    settings_from_mapping,
    supervisor_stagger_sleep,
)


def test_account_daily_limits_are_stable_per_day():
    uid = "user@example.com"
    d = date(2026, 6, 15)
    a1 = account_daily_application_limit(
        user_id=uid, bot_id="1", base=40, jitter=12, on_date=d
    )
    a2 = account_daily_application_limit(
        user_id=uid, bot_id="2", base=40, jitter=12, on_date=d
    )
    assert a1 == account_daily_application_limit(
        user_id=uid, bot_id="1", base=40, jitter=12, on_date=d
    )
    assert 28 <= a1 <= 52
    assert 28 <= a2 <= 52
    assert a1 != a2 or "1" == "2"


def test_effective_daily_limit_smart_mode():
    settings = settings_from_mapping(
        {
            "smart_rate_limiting": True,
            "max_applications_per_day": 40,
            "rate_limit_daily_jitter": 12,
        }
    )
    cap = effective_daily_limit(settings, user_id="u@test.com", bot_id="1")
    assert 28 <= cap <= 52


def test_supervisor_stagger_uses_random_range_when_enabled():
    settings = settings_from_mapping(
        {
            "smart_rate_limiting": True,
            "rate_limit_delay_min_sec": 12,
            "rate_limit_delay_max_sec": 44,
        }
    )
    for _ in range(20):
        delay = supervisor_stagger_sleep(settings)
        assert 12 <= delay <= 44


def test_supervisor_stagger_legacy_when_disabled():
    settings = settings_from_mapping({"smart_rate_limiting": False})
    assert supervisor_stagger_sleep(settings) == 15.0
