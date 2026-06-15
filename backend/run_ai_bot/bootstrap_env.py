"""
Shared imports and environment setup for the job applier (matches legacy runAiBot top-of-file).
Imported first by state.py and feature modules; must not import run_ai_bot.state (avoid cycles).
"""

import csv
import json
import os
import re
import sys
import tempfile

csv.field_size_limit(1000000)

# Display-safe pyautogui shim: real dialogs on desktop, logged no-ops on
# headless servers (raw `import pyautogui` crashes without a display).
from modules import gui_safe as pyautogui

from random import choice, shuffle, randint
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    NoSuchWindowException,
    ElementNotInteractableException,
    WebDriverException,
    StaleElementReferenceException,
    InvalidSessionIdException,
)

from config.config_bridge import *

from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.validator import validate_config

if use_AI:
    from modules.ai.openaiConnections import (
        ai_create_openai_client,
        ai_answer_question,
        ai_close_openai_client,
    )
    from modules.ai.deepseekConnections import (
        deepseek_create_client,
        deepseek_answer_question,
    )
    from modules.ai.geminiConnections import (
        gemini_create_client,
        gemini_answer_question,
    )

from typing import Literal

from selenium.webdriver.common.action_chains import ActionChains

from db_manager import db
from services.storage import storage_service
