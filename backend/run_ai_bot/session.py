"""Cookie persistence and DB application logging."""

import os

from run_ai_bot.bootstrap_env import *
from run_ai_bot.state import *


def _cookie_store_ids():
    """Dashboard users may have cookies seeded under local-user or their own id."""
    ln_user = (os.getenv("LINKEDIN_USERNAME") or "").strip().lower()
    ids = []
    if linkedin_cookie_store_id:
        ids.append(linkedin_cookie_store_id)
    if ln_user:
        legacy = f"local-user::linkedin::{ln_user}"
        if legacy not in ids:
            ids.append(legacy)
    if user_id and user_id not in ("local-user",):
        alt = f"{user_id}::linkedin::{ln_user}" if ln_user else user_id
        if alt not in ids:
            ids.append(alt)
    return ids


def save_cookies():
    """Saves current cookies to a file."""
    try:
        cookies = driver.get_cookies()
        for store_id in _cookie_store_ids():
            db.set_user_session(store_id, cookies)
        print_lg("Session cookies saved successfully!")
    except Exception as e:
        print_lg("Failed to save cookies!", e)


def load_cookies():
    """Loads cookies from file and refreshes the page."""
    cookies = None
    for store_id in _cookie_store_ids():
        cookies = db.get_user_session(store_id)
        if cookies:
            print_lg(f"Loaded session cookies from {store_id}")
            break
    if cookies:
        try:
            if "linkedin.com" not in driver.current_url:
                driver.get("https://www.linkedin.com")

            for cookie in cookies:
                if "expiry" in cookie:
                    cookie["expiry"] = int(cookie["expiry"])
                driver.add_cookie(cookie)

            print_lg("Cookies loaded. Refreshing session...")
            driver.refresh()
            buffer(2)
        except Exception as e:
            print_lg("Failed to load cookies. You may need to login manually.", e)


def log_to_db(status, **kwargs):
    """Helper to log application events to the database."""
    try:
        db.log_application(user_id, status=status, **kwargs)
    except Exception as e:
        print_lg(f"Failed to log to DB: {e}")
