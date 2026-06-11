"""Resolve the acting user for config/secrets endpoints.

The authoritative source is the NextAuth session cookie: when the request
carries one (same-origin deployments where nginx proxies both apps), we ask
the Next.js server who the user is. The client-supplied ``user_id`` query
param is only trusted when auth is not enforced (local single-user mode).

Env vars:
  REQUIRE_AUTH          "true" on public deployments — reject requests
                        without a valid session instead of falling back.
  NEXTAUTH_SESSION_URL  Where to verify sessions (default: local Next.js).
"""

import os

import httpx
from fastapi import HTTPException, Request

from db_manager import DEFAULT_USER

def _require_auth() -> bool:
    # Read lazily — module import can happen before load_dotenv() runs.
    return os.getenv("REQUIRE_AUTH", "").strip().lower() in ("1", "true", "yes")


def _session_url() -> str:
    return os.getenv(
        "NEXTAUTH_SESSION_URL", "http://127.0.0.1:3000/api/auth/session"
    )


async def resolve_user_id(request: Request, claimed_user_id: str | None = None) -> str:
    """Return the user namespace for this request.

    Order: verified session email > claimed user_id (non-enforced mode only)
    > DEFAULT_USER. Raises 401 when REQUIRE_AUTH is set and no valid session
    is presented.
    """
    cookie = request.headers.get("cookie")
    if cookie:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(_session_url(), headers={"cookie": cookie})
            if resp.status_code == 200:
                data = resp.json() or {}
                email = (data.get("user") or {}).get("email")
                if email:
                    return email
        except Exception:
            if _require_auth():
                raise HTTPException(
                    status_code=503, detail="Auth service unavailable"
                )

    if _require_auth():
        raise HTTPException(status_code=401, detail="Not authenticated")

    return (claimed_user_id or "").strip() or DEFAULT_USER
