import os
import logging

from app_paths import get_logs_dir


def _bot_file_log_path() -> str | None:
    bid = os.getenv("BOT_ID", "").strip()
    if not bid:
        return None
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in bid)
    return os.path.join(get_logs_dir(), f"bot-{safe}.txt")


def setup_logging():
    """Standard local logging only (no cloud backends)."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logger = logging.getLogger("linkedin_bot")
    logger.setLevel(log_level)

    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    file_path = _bot_file_log_path()
    if file_path:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        fh = logging.FileHandler(file_path, encoding="utf-8")
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


logger = setup_logging()
