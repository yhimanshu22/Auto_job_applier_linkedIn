"""Mix-in implementing LinkedIn sign-in flows with resilient selectors.

Why:
    Keep authentication logic isolated so the rest of the interaction mixins
    assume an authenticated session.

When:
    Mixed into :class:`LinkedInInteraction` and invoked during bot start-up or
    explicit re-login attempts.

How:
    Navigates to login, handles pre-login redirects, types credentials with
    human-like delays, and waits for feed indicators.
"""

import logging
from .. import config
import os
import time
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from services.linkedin_session import load_linkedin_cookies, save_linkedin_cookies


class LoginMixin:
    """Encapsulate LinkedIn authentication flows for reuse across workflows.

    Why:
        Keeps login-specific selectors and retries isolated from other mixins.

    When:
        Mixed into :class:`LinkedInInteraction` during bot initialisation or re-login attempts.

    How:
        Provides :meth:`login` which navigates, types credentials, and validates successful authentication.
    """

    def save_cookies(self):
        """Save current session cookies to the shared DB (user_sessions)."""
        try:
            cookies = self.driver.get_cookies()
            save_linkedin_cookies(cookies)
            logging.info("Saved session cookies to user_sessions")
        except Exception as e:
            logging.error(f"Failed to save cookies: {e}")

    def _looks_logged_in(self) -> bool:
        """Return True when the current page looks like an authenticated LinkedIn surface."""
        try:
            u = (self.driver.current_url or "").lower()
        except Exception:
            u = ""
        if any(
            frag in u
            for frag in (
                "/feed",
                "/mynetwork",
                "/messaging",
                "/notifications",
                "/learning",
            )
        ):
            return True
        if "/jobs" in u and "login" not in u:
            return True
        if "/in/" in u and "login" not in u and "signup" not in u:
            return True
        # Session can be valid on the marketing home without ``/feed`` in the URL.
        for by, sel in (
            (By.CSS_SELECTOR, "div.feed-identity-module"),
            (By.CSS_SELECTOR, "button[data-control-name='create_post']"),
            (By.CSS_SELECTOR, "div.share-box-feed-entry__avatar"),
            (By.CSS_SELECTOR, "img.global-nav__me-photo"),
            (By.CSS_SELECTOR, "button#global-nav__me"),
        ):
            try:
                if self.driver.find_elements(by, sel):
                    return True
            except Exception:
                continue
        return False

    def _ensure_window_focus(self) -> None:
        """Switch to the first window handle when UC leaves the session in a bad default."""
        try:
            handles = self.driver.window_handles
            if handles:
                self.driver.switch_to.window(handles[0])
        except Exception:
            pass

    def _get_resilient(self, url: str, *, attempts: int = 10, desc: str = "page") -> bool:
        """Navigate with retries when Chrome has not attached a window yet (Windows / uc)."""
        last_err: Exception | None = None
        for i in range(attempts):
            self._ensure_window_focus()
            try:
                self.driver.get(url)
                return True
            except NoSuchWindowException as e:
                last_err = e
                logging.warning(
                    "Browser window not ready (%s, attempt %s/%s); retrying.",
                    desc,
                    i + 1,
                    attempts,
                )
                if i == 2:
                    try:
                        self._ensure_window_focus()
                        self.driver.get("about:blank")
                    except Exception:
                        pass
                time.sleep(0.65 + 0.25 * i)
            except Exception as e:
                last_err = e
                break
        logging.error("Could not open %s (%s): %s", desc, url, last_err)
        return False

    def load_cookies(self):
        """Load session cookies from the shared DB and inject into browser.

        Returns:
            bool: True if cookies were loaded, False otherwise.
        """
        cookies = load_linkedin_cookies()
        if not cookies:
            return False

        try:
            if not self._get_resilient(
                config.LINKEDIN_BASE_URL, desc="LinkedIn (before cookies)"
            ):
                return False

            for cookie in cookies:
                if "expiry" in cookie:
                    cookie["expiry"] = int(cookie["expiry"])
                try:
                    self.driver.add_cookie(cookie)
                except Exception:
                    continue

            logging.info(f"Loaded {len(cookies)} cookies from user_sessions")
            return True
        except Exception as e:
            logging.error(f"Failed to load cookies: {e}")
            return False
            
    def login(self):
        """Authenticate the browser session using stored credentials.

        Why:
            Most downstream actions require an active LinkedIn session.

        When:
            Called during :class:`LinkedInBot` initialisation or when a session
            appears expired.

        How:
            Opens LinkedIn, handles redirects to the login form, types
            credentials with human delays, submits the form, and watches for feed
            indicators or verification prompts.

        Returns:
            bool: ``True`` on apparent success, ``False`` when credentials are
            missing or additional verification is required.
        """
        try:
            if not self._get_resilient(
                config.LINKEDIN_BASE_URL, desc="LinkedIn home (login)"
            ):
                return False
            logging.info("Navigating to LinkedIn login page")
            self.random_delay(config.MIN_PAGE_LOAD_DELAY, config.MAX_PAGE_LOAD_DELAY)

            using_bot_profile = bool(os.getenv("LINKDAPPLY_CHROME_PROFILE_DIR", "").strip())

            try:
                if using_bot_profile:
                    if not self._get_resilient(
                        config.LINKEDIN_FEED_URL, desc="LinkedIn feed (bot profile)"
                    ):
                        logging.warning(
                            "Could not open feed with job-bot Chrome profile; trying login flow."
                        )
                    else:
                        self.random_delay(
                            config.MIN_PAGE_LOAD_DELAY, config.MAX_PAGE_LOAD_DELAY
                        )
                        deadline = time.monotonic() + float(config.ELEMENT_TIMEOUT)
                        while time.monotonic() < deadline and not self._looks_logged_in():
                            time.sleep(0.25)
                        if self._looks_logged_in():
                            logging.info(
                                "Logged in via job-bot Chrome profile (no cookie DB needed)"
                            )
                            return True
                        logging.info(
                            "Job-bot Chrome profile present but session not logged in; "
                            "falling back to credentials / cookie store."
                        )
                elif self.load_cookies():
                    if not self._get_resilient(
                        config.LINKEDIN_FEED_URL, desc="LinkedIn feed (cookies)"
                    ):
                        logging.warning(
                            "Could not open feed after loading cookies (window not ready or "
                            "closed). Trying standard login."
                        )
                    else:
                        self.random_delay(config.MIN_PAGE_LOAD_DELAY, config.MAX_PAGE_LOAD_DELAY)
                        deadline = time.monotonic() + float(config.ELEMENT_TIMEOUT)
                        while time.monotonic() < deadline and not self._looks_logged_in():
                            time.sleep(0.25)

                        if self._looks_logged_in():
                            logging.info("Successfully logged in using stored cookies")
                            return True

                        logging.info(
                            "Cookie session expired or invalid, proceeding to standard login"
                        )

                if self._looks_logged_in():
                    logging.info("Already logged in to LinkedIn")
                    self.save_cookies()
                    return True
            except Exception as e:
                logging.debug("Cookie / pre-login check: %s", e, exc_info=True)

            try:
                sign_in_button = WebDriverWait(self.driver, config.SHORT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='signin']"))
                )
                sign_in_button.click()
                logging.info("Clicked sign-in button")
                self.random_delay()
            except Exception:
                logging.info("No sign-in button found, likely already on login page")

            if not any(x in self.driver.current_url.lower() for x in ["login", "signin"]):
                logging.warning(f"Not on login page. Current URL: {self.driver.current_url}")
                if not self._get_resilient(
                    config.LINKEDIN_LOGIN_URL, desc="LinkedIn login form"
                ):
                    return False
                self.random_delay()

            username_selectors = [
                "input#username",
                "input[name='session_key']",
                "input[autocomplete='username']",
                # Newer login layout: random ids, no name attribute.
                "input[autocomplete^='username']",
                "input[type='email']",
            ]
            username_field = self._find_element_from_selectors(username_selectors, By.CSS_SELECTOR)
            if not username_field:
                logging.error("Could not find username field")
                return False

            username = config.LINKEDIN_USERNAME
            password = config.LINKEDIN_PASSWORD
            if not username or not password:
                logging.error("LinkedIn credentials not found in environment variables.")
                return False

            self.random_delay(0.5, 1.5)
            self._type_with_human_delays(username_field, username)

            password_selectors = [
                "input#password",
                "input[name='session_password']",
                "input[autocomplete='current-password']",
                # Newer login layout: random ids, no name attribute.
                "input[autocomplete^='current-password']",
                "input[type='password']",
            ]
            password_field = self._find_element_from_selectors(password_selectors, By.CSS_SELECTOR)
            if not password_field:
                logging.error("Could not find password field")
                return False

            self.random_delay(0.5, 1)
            self._type_with_human_delays(password_field, password)

            sign_in_selectors = [
                "button[type='submit']",
                "button.sign-in-form__submit-button",
                "button[data-litms-control-urn='login-submit']",
            ]
            sign_in_btn = self._find_element_from_selectors(sign_in_selectors, By.CSS_SELECTOR)
            if not sign_in_btn:
                logging.error("Could not find sign-in button")
                return False
            sign_in_btn.click()
            logging.info("Clicked login button")
            self.random_delay(3, 5)

            try:
                WebDriverWait(self.driver, config.SHORT_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input#input__phone_verification_pin"))
                )
                logging.warning("Verification code required. Check your phone.")
                return False
            except Exception:
                logging.info("Verification code not required or error occurred.")

            if self._looks_logged_in():
                logging.info("Successfully logged in to LinkedIn")
                self.save_cookies()
                return True

            success_indicators = [
                (By.CSS_SELECTOR, "div.feed-identity-module"),
                (By.CSS_SELECTOR, "button[data-control-name='create_post']"),
                (By.XPATH, "//button[contains(.,'Start a post')]"),
                (By.CSS_SELECTOR, "div.share-box-feed-entry__avatar"),
            ]
            for selector_type, selector in success_indicators:
                try:
                    WebDriverWait(self.driver, config.ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    logging.info("Successfully logged in to LinkedIn")
                    self.save_cookies()  # Save cookies after success
                    return True
                except Exception:
                    continue

            if "feed" in self.driver.current_url.lower():
                logging.info("Successfully logged in to LinkedIn (URL check)")
                self.save_cookies()  # Save cookies after success
                return True

            logging.error(f"Login might have failed. Current URL: {self.driver.current_url}")
            return False
        except Exception as e:
            logging.error(f"Login failed: {e}", exc_info=True)
            return False
