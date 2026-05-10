"""Cookie persistence and DB application logging."""

from run_ai_bot.bootstrap_env import *
from run_ai_bot.state import *


def save_cookies():
    """Saves current cookies to a file."""
    try:
        db.set_user_session(linkedin_cookie_store_id, driver.get_cookies())
        print_lg("Session cookies saved successfully!")
    except Exception as e:
        print_lg("Failed to save cookies!", e)


def load_cookies():
    """Loads cookies from file and refreshes the page."""
    cookies = db.get_user_session(linkedin_cookie_store_id)
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
