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

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.join(_BACKEND_DIR, "config")
for _path in (_CONFIG_DIR, _BACKEND_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from dotenv import load_dotenv

load_dotenv(os.path.join(_BACKEND_DIR, ".env"))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from services.linkedin_session import save_linkedin_cookies


def main(linkedin_email: str) -> None:
    user_id = (os.getenv("USER_ID") or "").strip()
    if not user_id:
        raise SystemExit("Set USER_ID to your dashboard login email (e.g. you@gmail.com).")

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

    time.sleep(3)
    cookies = driver.get_cookies()
    save_linkedin_cookies(cookies, user_id=user_id, linkedin_username=linkedin_email)
    store_id = f"{user_id}::linkedin::{linkedin_email.lower()}"
    print(f"Saved {len(cookies)} cookies to user_sessions as {store_id!r}")
    driver.quit()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
