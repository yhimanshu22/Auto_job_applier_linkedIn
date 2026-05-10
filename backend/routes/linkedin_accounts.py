from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db_manager import db
from services.linkedin_env import (
    count_linkedin_accounts,
    preview_env_with_dashboard_credentials,
)

router = APIRouter(prefix="/api", tags=["linkedin-accounts"])


class LinkedInExtraRow(BaseModel):
    username: str = ""
    password: str = ""


class LinkedInAccountsSave(BaseModel):
    primary_username: str = ""
    primary_password: str = ""
    extras: list[LinkedInExtraRow] = Field(default_factory=list)


@router.get("/linkedin-accounts")
async def get_linkedin_accounts():
    """LinkedIn accounts stored for the bot (passwords not echoed)."""
    try:
        s = db.get_all_by_category("secrets")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    extras_raw = s.get("linkedin_extra_accounts")
    if not isinstance(extras_raw, list):
        extras_raw = []

    extras_out = []
    for row in extras_raw:
        if isinstance(row, dict) and row.get("username"):
            extras_out.append(
                {
                    "username": str(row.get("username", "")),
                    "password_set": bool(row.get("password")),
                }
            )

    return {
        "primary_username": (s.get("username") or ""),
        "primary_password_set": bool(s.get("password")),
        "extras": extras_out,
    }


@router.post("/linkedin-accounts")
async def save_linkedin_accounts(body: LinkedInAccountsSave):
    """Save primary + additional LinkedIn accounts (password optional = keep previous)."""
    try:
        existing = db.get_all_by_category("secrets")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    db.set_config("username", body.primary_username.strip(), "secrets")

    if body.primary_password.strip():
        db.set_config("password", body.primary_password, "secrets")

    old_extras = existing.get("linkedin_extra_accounts")
    if not isinstance(old_extras, list):
        old_extras = []

    old_by_username = {}
    for row in old_extras:
        if isinstance(row, dict) and row.get("username"):
            old_by_username[str(row["username"]).strip().lower()] = row

    merged: list[dict] = []
    for row in body.extras:
        u = row.username.strip()
        if not u:
            continue
        pw = row.password
        if not pw:
            prev = old_by_username.get(u.lower())
            if prev and prev.get("password"):
                pw = prev.get("password")
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Password required for LinkedIn account {u} (new account).",
                )
        merged.append({"username": u, "password": pw})

    db.set_config("linkedin_extra_accounts", merged, "secrets")
    return {
        "status": "saved",
        "account_count": count_linkedin_accounts(preview_env_with_dashboard_credentials()),
    }
