"""App-side LLM call caps (per user + per API key) to limit burn if a key leaks."""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Callable

log = logging.getLogger(__name__)


class LLMRateLimitExceeded(Exception):
    """Raised when an LLM request would exceed configured caps."""


@dataclass(frozen=True)
class LLMRateLimitSettings:
    enabled: bool = True
    max_per_minute: int = 6
    max_per_hour: int = 40
    max_per_day: int = 120
    max_key_per_minute: int = 10
    max_key_per_hour: int = 60
    max_key_per_day: int = 200


def _coerce_int(val, default: int) -> int:
    if isinstance(val, bool):
        return default
    if isinstance(val, int):
        return val
    if isinstance(val, str) and val.strip().lstrip("-").isdigit():
        return int(val.strip())
    return default


def _env_truthy(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def settings_from_env() -> LLMRateLimitSettings:
    return LLMRateLimitSettings(
        enabled=_env_truthy("LLM_RATE_LIMIT_ENABLED", True),
        max_per_minute=_coerce_int(os.getenv("LLM_MAX_CALLS_PER_MINUTE"), 6),
        max_per_hour=_coerce_int(os.getenv("LLM_MAX_CALLS_PER_HOUR"), 40),
        max_per_day=_coerce_int(os.getenv("LLM_MAX_CALLS_PER_DAY"), 120),
        max_key_per_minute=_coerce_int(os.getenv("LLM_MAX_KEY_CALLS_PER_MINUTE"), 10),
        max_key_per_hour=_coerce_int(os.getenv("LLM_MAX_KEY_CALLS_PER_HOUR"), 60),
        max_key_per_day=_coerce_int(os.getenv("LLM_MAX_KEY_CALLS_PER_DAY"), 200),
    )


def settings_from_mapping(cfg: dict | None) -> LLMRateLimitSettings:
    cfg = cfg or {}
    enabled = cfg.get("llm_rate_limit_enabled")
    if enabled is None:
        enabled = True
    else:
        enabled = bool(enabled)
    return LLMRateLimitSettings(
        enabled=enabled,
        max_per_minute=_coerce_int(cfg.get("llm_max_calls_per_minute"), 6),
        max_per_hour=_coerce_int(cfg.get("llm_max_calls_per_hour"), 40),
        max_per_day=_coerce_int(cfg.get("llm_max_calls_per_day"), 120),
        max_key_per_minute=_coerce_int(cfg.get("llm_max_key_calls_per_minute"), 10),
        max_key_per_hour=_coerce_int(cfg.get("llm_max_key_calls_per_hour"), 60),
        max_key_per_day=_coerce_int(cfg.get("llm_max_key_calls_per_day"), 200),
    )


def _db_path() -> str:
    from app_paths import get_runtime_writable_root

    return os.path.join(get_runtime_writable_root(), "data.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_rate_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_llm_rate_scope_time "
        "ON llm_rate_events (scope, created_at)"
    )


def _count_since(conn: sqlite3.Connection, scope: str, since: float) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM llm_rate_events WHERE scope = ? AND created_at >= ?",
        (scope, since),
    ).fetchone()
    return int(row[0]) if row else 0


def _key_fingerprint(api_key: str) -> str:
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    return digest[:24]


def _resolve_api_key(explicit: str | None, provider: str) -> str | None:
    if explicit and explicit.strip() and explicit.strip().lower() not in (
        "ollama",
        "your_api_key",
    ):
        return explicit.strip()
    prov = (provider or "").strip().lower()
    env_map = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "grok": "GROK_API_KEY",
    }
    env_name = env_map.get(prov, "LLM_API_KEY")
    val = (os.getenv(env_name) or "").strip()
    if not val or val.lower() == "ollama":
        return None
    return val


def acquire_llm_call_slot(
    *,
    user_id: str | None = None,
    api_key: str | None = None,
    provider: str = "llm",
) -> None:
    """
    Record one LLM call unless a per-user or per-API-key cap would be exceeded.

    Caps only apply to traffic through this app (subprocesses using the shared DB).
    Direct calls to Google/OpenAI with a stolen key are not blocked here.
    """
    settings = settings_from_env()
    if not settings.enabled:
        return

    uid = (user_id or os.getenv("USER_ID") or "").strip() or "_anonymous"
    now = time.time()
    key = _resolve_api_key(api_key, provider)

    user_checks: list[tuple[int, int, str]] = [
        (60, settings.max_per_minute, "minute"),
        (3600, settings.max_per_hour, "hour"),
        (86400, settings.max_per_day, "day"),
    ]
    key_checks: list[tuple[int, int, str]] = [
        (60, settings.max_key_per_minute, "minute"),
        (3600, settings.max_key_per_hour, "hour"),
        (86400, settings.max_key_per_day, "day"),
    ]

    scopes_user = [f"user:{uid}"]
    scopes_key: list[str] = []
    if key:
        scopes_key.append(f"key:{_key_fingerprint(key)}")

    with _connect() as conn:
        _ensure_table(conn)
        conn.execute("BEGIN IMMEDIATE")
        try:
            for scope in scopes_user:
                for window_sec, limit, label in user_checks:
                    if limit <= 0:
                        continue
                    if _count_since(conn, scope, now - window_sec) >= limit:
                        raise LLMRateLimitExceeded(
                            f"LLM rate limit: {limit} calls per {label} "
                            f"(user cap). Try again later or adjust limits in Automation settings."
                        )
            for scope in scopes_key:
                for window_sec, limit, label in key_checks:
                    if limit <= 0:
                        continue
                    if _count_since(conn, scope, now - window_sec) >= limit:
                        raise LLMRateLimitExceeded(
                            f"LLM rate limit: {limit} calls per {label} "
                            f"(API key cap). Key may be overused — rotate the key if unexpected."
                        )
            for scope in scopes_user + scopes_key:
                conn.execute(
                    "INSERT INTO llm_rate_events (scope, created_at) VALUES (?, ?)",
                    (scope, now),
                )
            if int(now) % 17 == 0:
                conn.execute(
                    "DELETE FROM llm_rate_events WHERE created_at < ?",
                    (now - 86400 * 3,),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def with_llm_rate_limit(fn: Callable[..., object], *, provider: str, api_key: str | None = None):
    """Decorator-style helper for one-off wrappers."""

    def wrapper(*args, **kwargs):
        acquire_llm_call_slot(api_key=api_key, provider=provider)
        return fn(*args, **kwargs)

    return wrapper