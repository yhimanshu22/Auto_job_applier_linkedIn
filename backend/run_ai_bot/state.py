"""Runtime globals for the applier (formerly module-level state in runAiBot.py)."""

import os
import re

from run_ai_bot.bootstrap_env import *

# --- identity / session ids ---
user_id = os.getenv("USER_ID", "local-user")
_ln_user = os.getenv("LINKEDIN_USERNAME", "").strip()
linkedin_cookie_store_id = (
    f"{user_id}::linkedin::{_ln_user.lower()}" if _ln_user else user_id
)
is_admin = user_id == "local-user" or os.getenv("USER_EMAIL") == "himu09854@gmail.com"

if run_in_background == True:
    pause_at_failed_question = False
    pause_before_submit = False
    run_non_stop = False

first_name = first_name.strip()
middle_name = middle_name.strip()
last_name = last_name.strip()
full_name = (
    first_name + " " + middle_name + " " + last_name
    if middle_name
    else first_name + " " + last_name
)

useNewResume = True
randomly_answered_questions = set()

tabs_count = 1
easy_applied_count = 0
external_jobs_count = 0
failed_count = 0
skip_count = 0
dailyEasyApplyLimitReached = False

re_experience = re.compile(
    r"[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?", re.IGNORECASE
)

desired_salary_lakhs = str(round(desired_salary / 100000, 2))
desired_salary_monthly = str(round(desired_salary / 12, 2))
desired_salary = str(desired_salary)

current_ctc_lakhs = str(round(current_ctc / 100000, 2))
current_ctc_monthly = str(round(current_ctc / 12, 2))
current_ctc = str(current_ctc)

notice_period_months = str(notice_period // 30)
notice_period_weeks = str(notice_period // 7)
notice_period = str(notice_period)

aiClient = None
about_company_for_ai = None

chatGPT_tab = False
linkedIn_tab = False
