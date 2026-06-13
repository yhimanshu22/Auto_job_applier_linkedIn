"""LinkedIn login / session checks."""

from run_ai_bot.bootstrap_env import *
from run_ai_bot.session import load_cookies, save_cookies
from run_ai_bot.state import *

from modules.human_actions import human_move_and_click, human_type_text


def is_logged_in_LN() -> bool:
    if driver.current_url == "https://www.linkedin.com/feed/":
        return True
    if try_linkText(driver, "Sign in"):
        return False
    # contains(., ...) also matches text nested in <span> (new login layout);
    # click=False — this is a presence check, not an action.
    if try_xp(driver, '//button[@type="submit" and contains(., "Sign in")]', False):
        return False
    if try_linkText(driver, "Join now"):
        return False
    print_lg("Didn't find Sign in link, so assuming user is logged in!")
    return True


def _first_visible(elements):
    for el in elements:
        try:
            if el.is_displayed():
                return el
        except Exception:
            continue
    return None


def _find_login_input(kind: str):
    """Locate the username/password input across login page variants.

    Legacy layout has ``id="username"`` / ``id="password"``. The newer layout
    uses random React ids and no name attribute, so we fall back to matching
    by input type / autocomplete on the first *visible* candidate.
    """
    if kind == "username":
        legacy_id = "username"
        css_fallbacks = [
            "input[name='session_key']",
            "input[type='email']",
            "input[autocomplete^='username']",
        ]
    else:
        legacy_id = "password"
        css_fallbacks = [
            "input[name='session_password']",
            "input[type='password']",
            "input[autocomplete^='current-password']",
        ]

    try:
        return driver.find_element(By.ID, legacy_id)
    except Exception:
        pass
    for sel in css_fallbacks:
        el = _first_visible(driver.find_elements(By.CSS_SELECTOR, sel))
        if el is not None:
            return el
    return None


def _find_sign_in_button():
    # Legacy: button text directly inside the element.
    try:
        return driver.find_element(
            By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]'
        )
    except Exception:
        pass
    # New layout: text nested in a child span.
    try:
        return driver.find_element(
            By.XPATH, '//button[@type="submit" and contains(., "Sign in")]'
        )
    except Exception:
        pass
    return _first_visible(driver.find_elements(By.CSS_SELECTOR, "button[type='submit']"))


def login_LN() -> None:
    driver.get("https://www.linkedin.com/login")
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
        username_field = _find_login_input("username")
        if username_field is not None:
            username_field.clear()
            human_type_text(username_field, username)
        else:
            print_lg("Couldn't find username field.")
        password_field = _find_login_input("password")
        if password_field is not None:
            password_field.clear()
            human_type_text(password_field, password)
        else:
            print_lg("Couldn't find password field.")
        sign_in_btn = _find_sign_in_button()
        if sign_in_btn is None:
            raise NoSuchElementException("Sign in button not found")
        human_move_and_click(driver, sign_in_btn)
        buffer(3)
    except Exception:
        try:
            profile_button = find_by_class(driver, "profile__details")
            human_move_and_click(driver, profile_button)
        except Exception:
            print_lg("Couldn't Login!")

    try:
        wait.until(EC.url_to_be("https://www.linkedin.com/feed/"))
        save_cookies()
        print_lg("Login successful!")
        return
    except Exception:
        try:
            wait.until(EC.url_contains("/feed"))
            save_cookies()
            print_lg("Login successful!")
            return
        except Exception:
            pass
        print_lg(
            "Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!"
        )
        manual_login_retry(is_logged_in_LN, 2)
        if is_logged_in_LN():
            save_cookies()
