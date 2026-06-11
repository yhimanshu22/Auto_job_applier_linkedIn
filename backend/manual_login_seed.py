"""Seed a LinkedIn session into the DB by logging in manually, locally.

Opens a visible Chrome window at the LinkedIn login page. Log in by hand
(solve any captcha / OTP). The script polls until the feed loads, then saves
the cookies into the ``user_sessions`` table — pointed at production when
DATABASE_URL is set — under the same store id the server bot uses.

Usage:
    USER_ID=you@gmail.com DATABASE_URL=postgres://... \
        uv run python manual_login_seed.py linkedin-account@email.com
"""

import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from db_manager import db


def main(linkedin_email: str) -> None:
    user_id = os.getenv("USER_ID", "local-user")
    # Save under both the dashboard user id and the legacy local-user id,
    # so the server bot finds the session regardless of how it was started.
    store_ids = {
        f"{user_id}::linkedin::{linkedin_email.lower()}",
        f"local-user::linkedin::{linkedin_email.lower()}",
    }

    options = Options()
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.linkedin.com/login")

    print(f"Log in as {linkedin_email} in the Chrome window (captcha/OTP ok).")
    print("Waiting for the LinkedIn feed... (up to 10 minutes)")

    deadline = time.monotonic() + 600
    logged_in = False
    while time.monotonic() < deadline:
        try:
            if "/feed" in driver.current_url:
                logged_in = True
                break
        except Exception:
            print("Browser window was closed before login completed.")
            sys.exit(1)
        time.sleep(2)

    if not logged_in:
        print("Timed out waiting for login.")
        driver.quit()
        sys.exit(1)

    time.sleep(3)  # let post-login cookies settle
    cookies = driver.get_cookies()
    for store_id in store_ids:
        db.set_user_session(store_id, cookies)
        print(f"Saved {len(cookies)} cookies to user_sessions as {store_id!r}")
    driver.quit()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
