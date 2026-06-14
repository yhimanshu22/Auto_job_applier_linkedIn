"""Cookie persistence and DB application logging."""

import os

from run_ai_bot.bootstrap_env import *
from run_ai_bot.state import *
from services.linkedin_session import load_linkedin_cookies, save_linkedin_cookies


def save_cookies():
    """Saves current cookies to the shared user_sessions table."""
    try:
        cookies = driver.get_cookies()
        ln_user = os.getenv("LINKEDIN_USERNAME", "").strip()
        save_linkedin_cookies(cookies, user_id=user_id, linkedin_username=ln_user)
        print_lg("Session cookies saved successfully!")
    except Exception as e:
        print_lg("Failed to save cookies!", e)


def load_cookies():
    """Loads cookies from the DB and refreshes the page."""
    ln_user = os.getenv("LINKEDIN_USERNAME", "").strip()
    cookies = load_linkedin_cookies(user_id=user_id, linkedin_username=ln_user)
    if cookies:
        print_lg(f"Loaded session cookies for {linkedin_cookie_store_id}")
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
