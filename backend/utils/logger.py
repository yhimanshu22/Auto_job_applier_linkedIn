import os
import logging


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

    return logger


logger = setup_logging()
