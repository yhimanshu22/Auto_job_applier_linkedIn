"""Centralised configuration for the LinkedIn automation bot.

Why:
    Keep secrets, selectors, runtime toggles, and logging conventions in a
    single module so the rest of the codebase can import consistent defaults.

When:
    Imported at startup by CLI scripts, automation classes, and helper modules
    needing environment-derived values or shared constants.

How:
    Loads environment variables via ``python-dotenv``, exposes typed constants
    for credentials, AI settings, Selenium timeouts, and logging, and provides
    helper functions for safe casting and logging configuration.
"""

import os
import logging
import pathlib
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LinkedIn credentials
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USE_GEMINI = (
    os.getenv("USE_GEMINI", "true").lower() == "true"
)  # Allow disabling AI via flag/env

# OpenAI settings (used for feed engagement commentary)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Which LLM powers LinkedIn comments / calendar / OpenAIClient helpers.
# Values: openai | gemini | grok | groq (case-insensitive). Empty = auto-pick
# from available keys (OpenAI → Gemini → Grok → Groq).
LINKEDIN_AI_PROVIDER = (os.getenv("LINKEDIN_AI_PROVIDER") or "").strip().lower()

# xAI Grok (OpenAI-compatible Chat Completions API)
GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_API_BASE = (os.getenv("GROK_API_BASE") or "https://api.x.ai/v1").rstrip("/")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-2-latest")

# Groq — optional dedicated vars, or reuse job-applier ``LLM_API_KEY`` when
# ``LLM_API_URL`` points at Groq. If ``LINKEDIN_AI_PROVIDER=groq``, ``LLM_API_KEY``
# is accepted even without "groq" in the URL.
_LLM_API_KEY = os.getenv("LLM_API_KEY")
_LLM_API_URL = (os.getenv("LLM_API_URL") or "").strip().rstrip("/")


def effective_groq_api_key() -> str | None:
    """Resolve the Groq API key from GROQ_* or shared LLM_* settings."""
    k = os.getenv("GROQ_API_KEY")
    if k:
        return k
    if not _LLM_API_KEY:
        return None
    if "groq" in _LLM_API_URL.lower():
        return _LLM_API_KEY
    if LINKEDIN_AI_PROVIDER == "groq":
        return _LLM_API_KEY
    return None


GROQ_API_BASE = (
    os.getenv("GROQ_API_BASE") or (_LLM_API_URL if _LLM_API_URL else "https://api.groq.com/openai/v1")
).rstrip("/")
GROQ_MODEL = os.getenv("GROQ_MODEL") or os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# Gemini model for OpenAIClient (comments / calendar); content posts use their own picker.
LINKEDIN_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def resolve_linkedin_ai_provider() -> str:
    """Pick the LLM backend for :class:`openai_client.OpenAIClient`."""
    if LINKEDIN_AI_PROVIDER in ("openai", "gemini", "grok", "groq"):
        return LINKEDIN_AI_PROVIDER
    if OPENAI_API_KEY:
        return "openai"
    if GEMINI_API_KEY:
        return "gemini"
    if GROK_API_KEY:
        return "grok"
    if effective_groq_api_key():
        return "groq"
    return "openai"


def has_linkedin_llm_credentials() -> bool:
    """True when at least one configured provider has the keys it needs."""
    p = resolve_linkedin_ai_provider()
    if p == "openai":
        return bool(OPENAI_API_KEY)
    if p == "gemini":
        return bool(GEMINI_API_KEY)
    if p == "grok":
        return bool(GROK_API_KEY)
    if p == "groq":
        return bool(effective_groq_api_key())
    return False

# Project marketing defaults
MARKETING_MODE = os.getenv("MARKETING_MODE", "true").lower() == "true"
PROJECT_NAME = os.getenv("PROJECT_NAME", "LinkedIn Bot")
PROJECT_URL = os.getenv("PROJECT_URL", "https://github.com/joeygoesgrey/linkedln-bot")
PROJECT_PITCH = os.getenv(
    "PROJECT_PITCH",
    "Human-like LinkedIn automation that posts, schedules, uploads media, tags people, and runs AI-powered engagement loops with detailed logging.",
)
PROJECT_SHORT_PITCH = os.getenv(
    "PROJECT_SHORT_PITCH",
    "Open-source LinkedIn automation toolkit for human-like posting and AI engagement.",
)
PROJECT_CONTEXT = os.getenv(
    "PROJECT_CONTEXT",
    "LinkedIn Bot is an MIT-licensed automation toolkit that drives the LinkedIn web UI with Selenium, supports posting, scheduling, media uploads, and mentions, and uses OpenAI/Gemini for AI-assisted engagement while logging every step and respecting human-like pacing.",
)
PROJECT_TAGLINE = os.getenv(
    "PROJECT_TAGLINE", f"{PROJECT_PITCH} Grab the code: {PROJECT_URL}"
)

# Comment persona: sound human; optional resume / single allowed GitHub profile
def _normalize_github_username(raw: str | None) -> str:
    s = (raw or "").strip()
    if not s:
        return "yhimanshu22"
    s = s.split("/")[-1].split("?")[0].strip()
    return s or "yhimanshu22"


LINKEDIN_GITHUB_USERNAME = _normalize_github_username(os.getenv("LINKEDIN_GITHUB_USERNAME"))
LINKEDIN_GITHUB_URL = f"https://github.com/{LINKEDIN_GITHUB_USERNAME}"
LINKEDIN_RESUME_URL = (os.getenv("LINKEDIN_RESUME_URL") or "").strip()
LINKEDIN_COMMENT_DISPLAY_NAME = (os.getenv("LINKEDIN_COMMENT_DISPLAY_NAME") or "").strip()
LINKEDIN_COMMENT_VOICE = os.getenv(
    "LINKEDIN_COMMENT_VOICE",
    "Write in first person as the real person behind this LinkedIn account — like you paused scrolling to leave a quick authentic thought. "
    "Vary rhythm and length; avoid corporate filler, buzzword stacks, and generic praise. No bullet lists.",
).strip()
# Comments: no "PS: check out …" toolkit plug unless explicitly enabled.
LINKEDIN_COMMENT_APPEND_PROJECT_CTA = (
    os.getenv("LINKEDIN_COMMENT_APPEND_PROJECT_CTA", "false").lower() == "true"
)
# Optional "comment for better reach" line — model adds only when tone fits (see prompt).
LINKEDIN_COMMENT_CFBR = os.getenv("LINKEDIN_COMMENT_CFBR", "true").lower() == "true"
LINKEDIN_COMMENT_FALLBACK = os.getenv(
    "LINKEDIN_COMMENT_FALLBACK",
    "Appreciate you putting this out there — following along.",
).strip()

# Browser settings
# Headless defaults to **false** because LinkedIn serves an empty / heavily-
# stripped feed to headless Chrome — engage runs end up scrolling for minutes
# without ever discovering a post. Users who really want headless can set
# ``HEADLESS=true`` via the dashboard settings panel.
HEADLESS = (
    os.getenv("HEADLESS", "false").lower() == "true"
)  # Run browser in headless mode, can be overridden
WINDOW_SIZE = (1920, 1080)  # Browser window size
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"

# URLs
LINKEDIN_BASE_URL = "https://www.linkedin.com/"
LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login/"

# Delays (in seconds)
MIN_TYPING_DELAY = 0.05  # Minimum delay between key presses
MAX_TYPING_DELAY = 0.15  # Maximum delay between key presses
MIN_ACTION_DELAY = 1  # Minimum delay between actions
MAX_ACTION_DELAY = 3  # Maximum delay between actions
MIN_PAGE_LOAD_DELAY = 2  # Minimum delay after page load
MAX_PAGE_LOAD_DELAY = 5  # Maximum delay after page load

# Selenium timeouts
ELEMENT_TIMEOUT = 10  # Maximum wait time for elements to appear (seconds)
SHORT_TIMEOUT = 5  # Shorter timeout for quick checks

# File paths
DEFAULT_TOPIC_FILE = "Topics.txt"
LOG_DIRECTORY = "logs"
CUSTOM_POSTS_FILE = os.getenv("CUSTOM_POSTS_FILE", "CustomPosts.txt")
COOKIE_FILE = os.getenv("LINKEDIN_COOKIE_PATH", "linkedin_cookies.pkl")  # legacy; cookies use DB

# Content limits
MAX_POST_LENGTH = 1300
ENABLE_TEXT_PREPROCESSING = (
    os.getenv("ENABLE_TEXT_PREPROCESSING", "false").lower() == "true"
)
SUMMARIZE_INPUT = os.getenv("SUMMARIZE_INPUT", "false").lower() == "true"


def _safe_float(value: str | None, default: float) -> float:
    """Convert an environment value to ``float`` with a resilient fallback.

    Why:
        Environment configuration often arrives as strings; this helper avoids
        repetitive try/except blocks throughout the module.

    When:
        Used during module import when computing float-based settings such as
        summarisation ratios.

    How:
        Attempts to cast ``value`` to ``float`` and returns ``default`` when the
        value is ``None`` or malformed.

    Args:
        value (str | None): Raw environment string to convert.
        default (float): Fallback value when conversion fails.

    Returns:
        float: Converted number or the provided default.
    """

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: str | None, default: int) -> int:
    """Convert an environment value to ``int`` with a resilient fallback.

    Why:
        Many runtime limits (token counts, char caps) are numeric but configured
        as strings; this helper standardises conversion and error handling.

    When:
        Called during module initialisation while populating integer constants.

    How:
        Attempts to cast ``value`` to ``int`` and returns ``default`` when the
        cast fails or the value is ``None``.

    Args:
        value (str | None): Raw environment string to convert.
        default (int): Fallback to use when conversion fails.

    Returns:
        int: Converted integer or the provided default.
    """

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


SUMMARIZE_RATIO = _safe_float(os.getenv("SUMMARIZE_RATIO"), 0.3)
MAX_INPUT_CHARS = _safe_int(os.getenv("MAX_INPUT_CHARS"), 3200)

# Mentions/typeahead capture (investigation/debugging)
# Why:
#     Enable saving the HTML of LinkedIn's mention suggestions popover
#     (e.g., container with class 'editor-typeahead-fetch') so we can inspect
#     structure and tune automation reliably when the UI changes.
# When:
#     During mention insertion flows; only if explicitly enabled via env.
# How:
#     LinkedInInteraction checks this flag and writes snapshots under
#     TYPEAHEAD_CAPTURE_DIR when suggestions appear.
CAPTURE_TYPEAHEAD_HTML = os.getenv("CAPTURE_TYPEAHEAD_HTML", "false").lower() == "true"
TYPEAHEAD_CAPTURE_DIR = os.getenv(
    "TYPEAHEAD_CAPTURE_DIR", str(pathlib.Path(LOG_DIRECTORY) / "typeahead")
)

# LinkedIn selectors (can be updated if the UI changes)
START_POST_SELECTORS = [
    "//button[contains(@class, 'share-box-feed-entry__trigger')]",
    "//button[contains(@aria-label, 'Start a post')]",
    "//div[contains(@class, 'share-box-feed-entry__trigger')]",
    "//button[contains(text(), 'Start a post')]",
    "//span[text()='Start a post']/ancestor::button",
    "//div[contains(@class, 'share-box')]",
]

POST_EDITOR_SELECTORS = [
    "//div[contains(@class, 'ql-editor')]",
    "//div[contains(@role, 'textbox')]",
    "//div[@data-placeholder='What do you want to talk about?']",
    "//div[contains(@aria-placeholder, 'What do you want to talk about?')]",
]

POST_BUTTON_SELECTORS = [
    "//button[contains(@class, 'share-actions__primary-action')]",
    "//button[text()='Post']",
    "//span[text()='Post']/parent::button",
    "//button[contains(@aria-label, 'Post')]",
]

# Default logging configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def configure_logging(log_level=None):
    """Initialise console and file logging for the automation suite.

    Why:
        Consistent logging is critical for diagnosing flaky UI interactions.
        Centralising setup ensures every script emits structured output.

    When:
        Called on module import with defaults and invoked again by the CLI
        entrypoint when the user requests ``--debug`` verbosity.

    How:
        Ensures the logs directory exists, creates a timestamped log file, and
        configures :mod:`logging` handlers for both file and stdout streams.

    Args:
        log_level (int | None): Explicit logging level; defaults to
            :data:`DEFAULT_LOG_LEVEL` when ``None``.

    Returns:
        None
    """
    level = log_level or DEFAULT_LOG_LEVEL

    # Ensure log directory exists
    log_dir = pathlib.Path(LOG_DIRECTORY)
    log_dir.mkdir(exist_ok=True)

    # Create unique log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"linkedin_bot_{timestamp}.log"

    # Configure logging to both file and console
    logging.basicConfig(
        level=level,
        format=DEFAULT_LOG_FORMAT,
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    logging.info(f"Logging configured at level {logging.getLevelName(level)}")
    logging.info(f"Log file: {log_file}")


# Initialize logging with default configuration (skip when parent task log is wired).
if not os.getenv("LINKDAPPLY_AUTOMATION_LOG", "").strip():
    configure_logging()
