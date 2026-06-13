"""Fetch subscription state from the cloud API (desktop sidecar + local SQLite)."""

from __future__ import annotations

import os

import httpx
from fastapi import HTTPException

from db_manager import db


def _cloud_api_base() -> str:
    return os.getenv("CLOUD_API_URL", "").strip().rstrip("/")


def _internal_key() -> str:
    return os.getenv("LINKDAPPLY_INTERNAL_KEY", "").strip()


def uses_cloud_subscription() -> bool:
    return bool(_cloud_api_base() and _internal_key())


def get_subscription_for_gating(user_id: str) -> dict | None:
    """Subscription for plan limits: cloud Postgres when configured, else local DB."""
    cloud = _cloud_api_base()
    key = _internal_key()
    if cloud and key:
        try:
            resp = httpx.get(
                f"{cloud}/api/billing/subscription-internal",
                params={"user_id": user_id},
                headers={"X-LinkdApply-Key": key},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                if not data or data.get("status") == "inactive" and data.get("plan") == "free":
                    return None
                return data
            if resp.status_code == 404:
                return None
            raise HTTPException(
                status_code=503,
                detail="Could not verify subscription with cloud billing service.",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Cloud subscription check failed: {exc}",
            ) from exc

    return db.get_user_subscription(user_id)
