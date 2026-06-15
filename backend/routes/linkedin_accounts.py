from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from db_manager import db
from services.linkedin_env import (
    count_linkedin_accounts,
    list_linkedin_accounts,
    preview_env_with_dashboard_credentials,
)
from utils.user_resolution import resolve_user_id

router = APIRouter(prefix="/api", tags=["linkedin-accounts"])


def _dashboard_stored_usernames(secrets: dict) -> set[str]:
    """Usernames saved in DB secrets (deletable via dashboard)."""
    out: set[str] = set()
    primary = (secrets.get("username") or "").strip().lower()
    if primary:
        out.add(primary)
    extras = secrets.get("linkedin_extra_accounts")
    if isinstance(extras, list):
        for row in extras:
            if isinstance(row, dict) and row.get("username"):
                out.add(str(row["username"]).strip().lower())
    return out


def _accounts_with_deletable(accounts: list[dict], secrets: dict) -> list[dict]:
    stored = _dashboard_stored_usernames(secrets)
    enriched = []
    for acc in accounts:
        row = dict(acc)
        row["deletable"] = str(acc.get("username", "")).strip().lower() in stored
        enriched.append(row)
    return enriched


class LinkedInExtraRow(BaseModel):
    username: str = ""
    password: str = ""


class LinkedInAccountsSave(BaseModel):
    primary_username: str = ""
    primary_password: str = ""
    extras: list[LinkedInExtraRow] = Field(default_factory=list)


@router.get("/linkedin-accounts")
async def get_linkedin_accounts(request: Request, user_id: str | None = None):
    """LinkedIn accounts stored for the bot (passwords not echoed)."""
    uid = await resolve_user_id(request, user_id)
    try:
        s = db.get_all_by_category("secrets", user_id=uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    env = preview_env_with_dashboard_credentials(user_id=uid)
    accounts = _accounts_with_deletable(
        list_linkedin_accounts(env=env, user_id=uid), s
    )

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
        "account_count": len(accounts),
        "accounts": accounts,
        "primary_username": (s.get("username") or ""),
        "primary_password_set": bool(s.get("password")),
        "extras": extras_out,
    }


@router.post("/linkedin-accounts")
async def save_linkedin_accounts(
    body: LinkedInAccountsSave, request: Request, user_id: str | None = None
):
    """Save primary + additional LinkedIn accounts (password optional = keep previous)."""
    uid = await resolve_user_id(request, user_id)
    try:
        existing = db.get_all_by_category("secrets", user_id=uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    primary_user = body.primary_username.strip()
    if not primary_user:
        raise HTTPException(status_code=400, detail="LinkedIn email is required.")

    db.set_config("username", primary_user, "secrets", user_id=uid)

    if body.primary_password.strip():
        db.set_config("password", body.primary_password, "secrets", user_id=uid)
    else:
        existing_pw = existing.get("password")
        if not existing_pw or not str(existing_pw).strip():
            raise HTTPException(
                status_code=400,
                detail="Password required for a new LinkedIn account.",
            )

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

    db.set_config("linkedin_extra_accounts", merged, "secrets", user_id=uid)
    return {
        "status": "saved",
        "account_count": count_linkedin_accounts(
            preview_env_with_dashboard_credentials(user_id=uid), user_id=uid
        ),
    }


@router.delete("/linkedin-accounts")
async def delete_linkedin_account(
    username: str, request: Request, user_id: str | None = None
):
    """Delete a stored LinkedIn account (primary or extra) by its email."""
    uid = await resolve_user_id(request, user_id)
    target = username.strip().lower()
    if not target:
        raise HTTPException(status_code=400, detail="username is required")

    try:
        s = db.get_all_by_category("secrets", user_id=uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    deleted = False

    if str(s.get("username") or "").strip().lower() == target:
        db.delete_config("username", "secrets", user_id=uid)
        db.delete_config("password", "secrets", user_id=uid)
        deleted = True

        extras = s.get("linkedin_extra_accounts")
        if isinstance(extras, list) and extras:
            first = extras[0]
            if isinstance(first, dict) and (first.get("username") or "").strip():
                db.set_config(
                    "username",
                    str(first["username"]).strip(),
                    "secrets",
                    user_id=uid,
                )
                if first.get("password"):
                    db.set_config("password", first["password"], "secrets", user_id=uid)
                db.set_config(
                    "linkedin_extra_accounts",
                    [row for row in extras[1:] if isinstance(row, dict)],
                    "secrets",
                    user_id=uid,
                )

    extras = s.get("linkedin_extra_accounts")
    if isinstance(extras, list):
        kept = [
            row
            for row in extras
            if not (
                isinstance(row, dict)
                and str(row.get("username", "")).strip().lower() == target
            )
        ]
        if len(kept) != len(extras):
            db.set_config("linkedin_extra_accounts", kept, "secrets", user_id=uid)
            deleted = True

    if not deleted:
        raise HTTPException(status_code=404, detail=f"No saved account {username}")

    return {
        "status": "deleted",
        "account_count": count_linkedin_accounts(
            preview_env_with_dashboard_credentials(user_id=uid), user_id=uid
        ),
    }
