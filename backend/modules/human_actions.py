"""
Variable pacing and non-instant UI actions for Selenium.

These helpers reduce rigid, clockwork timing and always-center clicks. They do not
guarantee any outcome on third-party sites; respect each site's terms and limits.
"""

from __future__ import annotations

import os
import random
import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


def _effective_bot_speed() -> int:
    try:
        from config.config_bridge import bot_speed

        speed_val = int(bot_speed)
    except Exception:
        speed_val = 5
    user_id = os.getenv("USER_ID", "local-user")
    is_priv = user_id == "local-user" or os.getenv("USER_EMAIL") == "himu09854@gmail.com"
    if is_priv:
        speed_val = max(speed_val, 9)
    return speed_val


def _pace_multiplier(speed_val: int) -> float:
    """Match helpers.buffer: higher speed setting => shorter pauses."""
    return max(0.05, (11 - speed_val) / 5.0)


def human_move_and_click(driver: WebDriver, element: WebElement) -> None:
    """
    Move with a slight offset approach, variable pauses, then click.
    Fast path (native .click) when bot_speed tier is >= 9.
    """
    speed_val = _effective_bot_speed()
    if speed_val >= 9:
        element.click()
        return

    mult = _pace_multiplier(speed_val)
    try:
        chain = ActionChains(driver)
        ox = random.randint(-14, 14)
        oy = random.randint(-14, 14)
        if ox != 0 or oy != 0:
            try:
                chain.move_to_element_with_offset(element, ox, oy)
                chain.pause(random.uniform(0.04, 0.15) * mult)
            except Exception:
                pass
        chain.move_to_element(element)
        chain.pause(random.triangular(0.06, 0.42, 0.13) * mult)
        if random.random() < 0.14:
            chain.pause(random.uniform(0.05, 0.26) * mult)
        chain.click()
        chain.perform()
    except Exception:
        element.click()


def human_type_text(element: WebElement, text: str | None) -> None:
    """
    Type text with irregular per-character delays. Long strings use scaled-down
    delays so cover letters do not take many minutes.
    """
    if text is None:
        text = ""
    text = str(text)
    speed_val = _effective_bot_speed()
    if speed_val >= 9:
        element.send_keys(text)
        return

    mult = _pace_multiplier(speed_val)
    n = max(len(text), 1)
    # Soften typing pace for long answers (textarea / cover letter).
    length_scale = max(0.14, min(1.0, 200 / n))

    for i, ch in enumerate(text):
        element.send_keys(ch)
        if ch in " \n\t.,;:!?":
            base = random.triangular(0.07, 0.48, 0.15)
        else:
            base = random.triangular(0.03, 0.26, 0.085)
        time.sleep(base * mult * length_scale)
        if random.random() < 0.045 and i > 2:
            time.sleep(random.uniform(0.12, 0.52) * mult * length_scale)

    time.sleep(random.uniform(0.04, 0.22) * mult)
