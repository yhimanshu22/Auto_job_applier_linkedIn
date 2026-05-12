"""Human-like UI interactions (delegates to shared Selenium helpers)."""

from selenium.webdriver.remote.webelement import WebElement

from run_ai_bot.bootstrap_env import *
from run_ai_bot.state import *

from modules.human_actions import human_move_and_click


def human_click(element: WebElement) -> None:
    human_move_and_click(driver, element)
