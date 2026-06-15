"""LinkedIn session cookies in SQLite (``user_sessions`` table).

Used by the LinkedIn automation framework (calendar / outreach UI). The job-applier
bot persists login in per-account Chrome profiles instead (``--user-data-dir``).
"""

from __future__ import annotations

import os

from db_manager import db


def cookie_store_ids(
    user_id: str | None = None,
    linkedin_username: str | None = None,
) -> list[str]:
    """Return store keys to try, newest preference first."""
    uid = (user_id or os.getenv("USER_ID") or "").strip()
    ln = (linkedin_username or os.getenv("LINKEDIN_USERNAME") or "").strip().lower()

    ids: list[str] = []
    if ln and uid:
        ids.append(f"{uid}::linkedin::{ln}")
    elif uid:
        ids.append(uid)
    return ids


def save_linkedin_cookies(
    cookies: list,
    *,
    user_id: str | None = None,
    linkedin_username: str | None = None,
) -> None:
    for store_id in cookie_store_ids(user_id, linkedin_username):
        db.set_user_session(store_id, cookies)


def load_linkedin_cookies(
    *,
    user_id: str | None = None,
    linkedin_username: str | None = None,
) -> list | None:
    for store_id in cookie_store_ids(user_id, linkedin_username):
        cookies = db.get_user_session(store_id)
        if cookies:
            return cookies
    return None
