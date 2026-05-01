import os
import logging
from google.cloud import logging as cloud_logging
from google.auth.exceptions import DefaultCredentialsError

def setup_cloud_logging():
    """
    Sets up Google Cloud Logging if in production and credentials exist.
    Otherwise falls back to standard local logging.
    """
    env = os.getenv("ENV", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Standard logger setup
    logger = logging.getLogger("linkedin_bot")
    logger.setLevel(log_level)
    
    # Local Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Cloud Logging Handler
    if env == "production":
        try:
            client = cloud_logging.Client()
            # Attaches the Google Cloud Logging handler to the root logger
            client.setup_logging()
            logger.info("Cloud Logging enabled.")
        except (DefaultCredentialsError, Exception) as e:
            logger.warning(f"Failed to initialize Cloud Logging: {e}. Using local logging.")
            
    return logger

# Global logger instance
logger = setup_cloud_logging()
