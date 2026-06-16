"""Resolve app version: env override → repo VERSION file → pyproject.toml."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BACKEND_DIR.parent


@lru_cache
def get_app_version() -> str:
    for key in ("LINKDAPPLY_VERSION", "APP_VERSION"):
        value = os.getenv(key, "").strip()
        if value:
            return value

    version_file = _REPO_ROOT / "VERSION"
    if version_file.is_file():
        text = version_file.read_text(encoding="utf-8").strip()
        if text:
            return text.splitlines()[0].strip()

    pyproject = _BACKEND_DIR / "pyproject.toml"
    if pyproject.is_file():
        match = re.search(
            r'^\s*version\s*=\s*["\']([^"\']+)["\']',
            pyproject.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        if match:
            return match.group(1)

    return "0.0.0"
