"""DB application logging for the job-applier bot.

LinkedIn login sessions are persisted in per-account Chrome profiles
(see ``modules/open_chrome.py`` ``--user-data-dir``), not in the cookie DB.
"""

from run_ai_bot.bootstrap_env import *
from run_ai_bot.state import *


def log_to_db(status, **kwargs):
    """Helper to log application events to the database."""
    try:
        db.log_application(user_id, status=status, **kwargs)
    except Exception as e:
        print_lg(f"Failed to log to DB: {e}")
