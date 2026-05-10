import os
from typing import Optional


def get_secret(secret_id: str, version_id: str = "latest") -> Optional[str]:
    """
    Reads secrets from environment variables only (no cloud backend).
    """
    return os.getenv(secret_id)


def load_all_secrets(secret_names: list[str]) -> None:
    """Ensures listed secret names are present in os.environ when set in the shell."""
    for name in secret_names:
        val = get_secret(name)
        if val:
            os.environ[name] = val
