"""Resolved backend install / bundle paths (same semantics as legacy server.get_base_path)."""

import os
import sys


def get_base_path() -> str:
    """Returns the base path for the application, handling both script and EXE modes."""
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
        if os.path.basename(base_path) == "dist":
            return os.path.dirname(base_path)
        return base_path
    return os.path.dirname(os.path.abspath(__file__))


def get_logs_dir() -> str:
    """Canonical runtime logs directory (always under get_base_path(), never cwd-relative)."""
    return os.path.join(get_base_path(), "logs")


def get_config_path(filename: str) -> str:
    return os.path.join(get_base_path(), "config", filename)
