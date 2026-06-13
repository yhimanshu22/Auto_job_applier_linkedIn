import os
import logging

from utils.debug_logs import bot_log_path


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

    bid = os.getenv("BOT_ID", "").strip()
    file_path = bot_log_path(bid) if bid else None
    if file_path:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        fh = logging.FileHandler(file_path, encoding="utf-8")
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


logger = setup_logging()
