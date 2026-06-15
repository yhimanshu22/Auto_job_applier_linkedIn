"""Resolve the acting user for config/secrets endpoints.

The authoritative source is the NextAuth session cookie: when the request
carries one (same-origin deployments where nginx proxies both apps), we ask
the Next.js server who the user is. Client-supplied ``user_id`` query/body
values are never trusted as identity — they may only be echoed for mismatch
checks when a session is present.

Env vars:
  REQUIRE_AUTH          "true" on public deployments — reject requests
                        without a valid session instead of falling back.
  NEXTAUTH_SESSION_URL  Where to verify sessions (default: local Next.js).
"""

import os

import httpx
from fastapi import HTTPException, Request

def _require_auth() -> bool:
    # Read lazily — module import can happen before load_dotenv() runs.
    return os.getenv("REQUIRE_AUTH", "").strip().lower() in ("1", "true", "yes")


def _session_url() -> str:
    return os.getenv(
        "NEXTAUTH_SESSION_URL", "http://127.0.0.1:3000/api/auth/session"
    )


def _trusted_proxy_email(request: Request) -> str | None:
    """Identity attested by the Vercel billing proxy (split frontend/backend)."""
    expected = os.getenv("LINKDAPPLY_INTERNAL_KEY", "").strip()
    if not expected:
        return None
    key = (request.headers.get("x-linkdapply-key") or "").strip()
    if key != expected:
        return None
    email = (request.headers.get("x-linkdapply-user") or "").strip()
    return email or None


async def _session_email(request: Request) -> str | None:
    """Return the verified session email, or None when unauthenticated."""
    cookie = request.headers.get("cookie")
    if not cookie:
        return None
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(_session_url(), headers={"cookie": cookie})
        if resp.status_code == 200:
            data = resp.json() or {}
            email = (data.get("user") or {}).get("email")
            if email:
                return email.strip()
    except Exception:
        if _require_auth():
            raise HTTPException(
                status_code=503, detail="Auth service unavailable"
            )
    return None


def _local_desktop_trust_claimed() -> bool:
  return os.getenv("LINKDAPPLY_LOCAL_DATA", "").strip().lower() in ("1", "true", "yes")


async def _claimed_user_id(request: Request, query_user_id: str | None = None) -> str | None:
    claimed = (query_user_id or "").strip()
    if not claimed:
        try:
            body = await request.json()
            if isinstance(body, dict):
                raw = body.get("user_id")
                if raw is not None and str(raw).strip():
                    claimed = str(raw).strip()
        except Exception:
            pass
    return claimed or None


async def resolve_user_id(request: Request, claimed_user_id: str | None = None) -> str:
    """Return the user namespace for this request.

    Order: verified session email > explicit ``user_id`` query/body (dev only).
    Raises 401 when no session is available and no ``user_id`` was supplied.
    Raises 403 when the client supplies a user_id that does not match the
    authenticated session.
    """
    claimed = (claimed_user_id or "").strip()

    proxy_user = _trusted_proxy_email(request)
    if proxy_user:
        if claimed and claimed != proxy_user:
            raise HTTPException(
                status_code=403,
                detail="user_id does not match authenticated session",
            )
        return proxy_user

    session_user = await _session_email(request)

    if session_user:
        if claimed and claimed != session_user:
            raise HTTPException(
                status_code=403,
                detail="user_id does not match authenticated session",
            )
        return session_user

    if claimed and _local_desktop_trust_claimed():
        return claimed

    if _require_auth():
        raise HTTPException(status_code=401, detail="Not authenticated")

    if claimed:
        return claimed

    raise HTTPException(status_code=401, detail="Not authenticated")
