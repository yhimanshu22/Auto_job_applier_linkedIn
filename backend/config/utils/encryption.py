"""Encrypt/decrypt sensitive config values at rest.

Requires ``ENCRYPTION_KEY`` — a Fernet key generated once and stored in env::

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Production deployments must set this (along with ``REQUIRE_AUTH=true``). There is
no built-in default key; missing configuration fails on first use.
"""

import os

from cryptography.fernet import Fernet, InvalidToken

_cipher_suite: Fernet | None = None


def _require_auth() -> bool:
    return os.getenv("REQUIRE_AUTH", "").strip().lower() in ("1", "true", "yes")


def _resolve_encryption_key() -> str:
    key = os.getenv("ENCRYPTION_KEY", "").strip()
    if key:
        return key

    hint = (
        "ENCRYPTION_KEY is not set. Generate one with: "
        'python -c "from cryptography.fernet import Fernet; '
        'print(Fernet.generate_key().decode())" '
        "and add it to backend/.env"
    )
    if _require_auth():
        raise RuntimeError(f"{hint} (required when REQUIRE_AUTH is enabled)")
    raise RuntimeError(hint)


def _get_cipher() -> Fernet:
    global _cipher_suite
    if _cipher_suite is None:
        _cipher_suite = Fernet(_resolve_encryption_key().encode())
    return _cipher_suite


def encrypt_data(data: str) -> str:
    """Encrypts a string and returns a base64 encoded string."""
    if not data:
        return data
    return _get_cipher().encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypts a base64 encoded string and returns the original string."""
    if not encrypted_data:
        return encrypted_data
    try:
        return _get_cipher().decrypt(encrypted_data.encode()).decode()
    except InvalidToken:
        # Plain-text legacy value — allows gradual migration.
        return encrypted_data
    except Exception:
        return encrypted_data
