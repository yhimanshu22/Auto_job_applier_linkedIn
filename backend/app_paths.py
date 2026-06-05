"""Resolved backend install / bundle paths (same semantics as legacy server.get_base_path)."""

import os
import sys


def get_base_path() -> str:
    """Install / bundle root (read-only under Program Files when packaged)."""
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
        if os.path.basename(base_path) == "dist":
            return os.path.dirname(base_path)
        return base_path
    return os.path.dirname(os.path.abspath(__file__))


def _ensure_packaged_runtime_subdirs(root: str) -> None:
    """CSV / uploads / Chrome expect these folders relative to the bot cwd."""
    for sub in ("logs", "all excels", "all resumes", "chrome_profiles", "cookies"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)


def get_runtime_writable_root() -> str:
    """
    Writable root for DB, logs, uploads, chrome_profiles, bot working directory.
    Set LINKDAPPLY_USER_DATA to override the writable data directory; otherwise uses the backend folder.
    """
    override = os.getenv("LINKDAPPLY_USER_DATA", "").strip()
    if override:
        os.makedirs(override, exist_ok=True)
        _ensure_packaged_runtime_subdirs(override)
        return override
    return get_base_path()


def get_logs_dir() -> str:
    """Logs under writable root (required when installed under Program Files)."""
    log_dir = os.path.join(get_runtime_writable_root(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_config_path(filename: str) -> str:
    """Bundled config templates (read-only in production installs)."""
    return os.path.join(get_base_path(), "config", filename)
