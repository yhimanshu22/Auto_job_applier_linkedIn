"""Human-like UI interactions."""

import os
from random import randint

from selenium.webdriver.common.action_chains import ActionChains

from run_ai_bot.bootstrap_env import *
from run_ai_bot.state import *


def human_click(element):
    try:
        _is_admin = (
            user_id == "local-user" or os.getenv("USER_EMAIL") == "himu09854@gmail.com"
        )

        from config.config_bridge import bot_speed

        try:
            speed_val = int(bot_speed)
        except Exception:
            speed_val = 5

        if _is_admin:
            speed_val = max(speed_val, 9)

        if speed_val >= 9:
            element.click()
            return

        ActionChains(driver).move_to_element(element).pause(randint(2, 6) / 20).click().perform()
    except Exception:
        element.click()
