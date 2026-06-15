import pytest
from fastapi import HTTPException

from utils import user_resolution as ur


@pytest.mark.asyncio
async def test_resolve_user_id_accepts_trusted_proxy(monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_INTERNAL_KEY", "test-internal-key")
    monkeypatch.setenv("REQUIRE_AUTH", "true")

    class _Req:
        headers = {
            "x-linkdapply-key": "test-internal-key",
            "x-linkdapply-user": "alice@example.com",
        }

    user = await ur.resolve_user_id(_Req(), "alice@example.com")
    assert user == "alice@example.com"


@pytest.mark.asyncio
async def test_resolve_user_id_rejects_spoofed_trusted_proxy(monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_INTERNAL_KEY", "test-internal-key")
    monkeypatch.setenv("REQUIRE_AUTH", "true")

    class _Req:
        headers = {
            "x-linkdapply-key": "test-internal-key",
            "x-linkdapply-user": "alice@example.com",
        }

    with pytest.raises(HTTPException) as exc:
        await ur.resolve_user_id(_Req(), "victim@example.com")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_resolve_user_id_uses_session_email(monkeypatch):
    async def _session(_request):
        return "alice@example.com"

    monkeypatch.setattr(ur, "_session_email", _session)
    user = await ur.resolve_user_id(None, "alice@example.com")
    assert user == "alice@example.com"


@pytest.mark.asyncio
async def test_resolve_user_id_rejects_spoofed_claim(monkeypatch):
    async def _session(_request):
        return "alice@example.com"

    monkeypatch.setattr(ur, "_session_email", _session)
    with pytest.raises(HTTPException) as exc:
        await ur.resolve_user_id(None, "victim@example.com")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_resolve_user_id_dev_mode_accepts_claimed(monkeypatch):
    monkeypatch.delenv("REQUIRE_AUTH", raising=False)

    async def _session(_request):
        return None

    monkeypatch.setattr(ur, "_session_email", _session)
    user = await ur.resolve_user_id(None, "dev@example.com")
    assert user == "dev@example.com"


@pytest.mark.asyncio
async def test_resolve_user_id_desktop_local_accepts_claimed(monkeypatch):
    monkeypatch.delenv("REQUIRE_AUTH", raising=False)
    monkeypatch.setenv("LINKDAPPLY_LOCAL_DATA", "true")

    async def _session(_request):
        return None

    monkeypatch.setattr(ur, "_session_email", _session)
    user = await ur.resolve_user_id(None, "desktop-user@example.com")
    assert user == "desktop-user@example.com"


@pytest.mark.asyncio
async def test_resolve_user_id_requires_auth_when_no_session_or_claim(monkeypatch):
    monkeypatch.delenv("REQUIRE_AUTH", raising=False)

    async def _session(_request):
        return None

    monkeypatch.setattr(ur, "_session_email", _session)
    with pytest.raises(HTTPException) as exc:
        await ur.resolve_user_id(None, None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_resolve_user_id_requires_auth_when_configured(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "true")

    async def _session(_request):
        return None

    monkeypatch.setattr(ur, "_session_email", _session)
    with pytest.raises(HTTPException) as exc:
        await ur.resolve_user_id(None, "anyone@example.com")
    assert exc.value.status_code == 401


def test_api_rejects_spoofed_user_id_query(client, auth_as):
    auth_as("alice@example.com")
    res = client.get(
        "/api/applications/stats",
        params={"user_id": "victim@example.com"},
    )
    assert res.status_code == 403
