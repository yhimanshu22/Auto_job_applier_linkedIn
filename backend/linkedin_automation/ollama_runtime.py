"""Detect local Ollama and pick a small model for feed analysis / comments."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_OLLAMA_MODEL = "llama3.2:1b"


def _ollama_root() -> str:
    base = (os.getenv("OLLAMA_API_BASE") or "http://127.0.0.1:11434/v1").strip().rstrip("/")
    if base.endswith("/v1"):
        return base[:-3]
    return base.rstrip("/")


def fetch_installed_models(*, timeout: float = 2.5) -> list[dict[str, Any]]:
    """Return models from ``GET /api/tags`` (empty when Ollama is offline)."""
    url = f"{_ollama_root()}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        payload = json.loads(raw)
        models = payload.get("models")
        return list(models) if isinstance(models, list) else []
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logging.debug("Ollama tags unavailable: %s", exc)
        return []


def pick_smallest_model(models: list[dict[str, Any]]) -> str | None:
    """Pick the smallest model by on-disk ``size`` (bytes) from Ollama's tag list."""
    if not models:
        return None

    def sort_key(item: dict[str, Any]) -> int:
        try:
            return int(item.get("size") or 0)
        except (TypeError, ValueError):
            return 0

    smallest = min(models, key=sort_key)
    name = smallest.get("name")
    return str(name).strip() if name else None


def ollama_available(*, timeout: float = 2.5) -> bool:
    return bool(fetch_installed_models(timeout=timeout))


def resolve_ollama_model() -> str:
    """Explicit ``OLLAMA_MODEL`` wins; else smallest installed tag; else default."""
    explicit = (os.getenv("OLLAMA_MODEL") or "").strip()
    if explicit:
        return explicit
    picked = pick_smallest_model(fetch_installed_models())
    if picked:
        return picked
    return DEFAULT_OLLAMA_MODEL