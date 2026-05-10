"""LinkedIn login / session checks."""

from run_ai_bot.bootstrap_env import *
from run_ai_bot.humanize import human_click
from run_ai_bot.session import load_cookies, save_cookies
from run_ai_bot.state import *


def is_logged_in_LN() -> bool:
    if driver.current_url == "https://www.linkedin.com/feed/":
        return True
    if try_linkText(driver, "Sign in"):
        return False
    if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'):
        return False
    if try_linkText(driver, "Join now"):
        return False
    print_lg("Didn't find Sign in link, so assuming user is logged in!")
    return True


def login_LN() -> None:
    driver.get("https://www.linkedin.com/login")
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
        try:
            text_input_by_ID(driver, "username", username, 1)
        except Exception:
            print_lg("Couldn't find username field.")
        try:
            text_input_by_ID(driver, "password", password, 1)
        except Exception:
            print_lg("Couldn't find password field.")
        driver.find_element(
            By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]'
        ).click()
    except Exception:
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception:
            print_lg("Couldn't Login!")

    try:
        wait.until(EC.url_to_be("https://www.linkedin.com/feed/"))
        save_cookies()
        print_lg("Login successful!")
        return
    except Exception:
        print_lg(
            "Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!"
        )
        manual_login_retry(is_logged_in_LN, 2)
        if is_logged_in_LN():
            save_cookies()
