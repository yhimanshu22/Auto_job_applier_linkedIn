import os

import pytest
from cryptography.fernet import Fernet

from utils import encryption as enc


@pytest.fixture(autouse=True)
def _reset_cipher(monkeypatch):
    enc._cipher_suite = None
    yield
    enc._cipher_suite = None


def test_encrypt_decrypt_roundtrip(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    assert enc.decrypt_data(enc.encrypt_data("secret")) == "secret"


def test_decrypt_returns_plaintext_legacy_values(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    assert enc.decrypt_data("not-encrypted") == "not-encrypted"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("REQUIRE_AUTH", raising=False)
    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY is not set"):
        enc.encrypt_data("x")


def test_missing_key_raises_when_require_auth(monkeypatch):
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    with pytest.raises(RuntimeError, match="REQUIRE_AUTH is enabled"):
        enc.encrypt_data("x")
