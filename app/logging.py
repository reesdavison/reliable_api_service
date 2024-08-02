import logging
from logging import getLogger

LOG_PREFIX = "reliable_api_service"


def get_logger(name):
    """name should come from __name__ in the file"""
    logger = getLogger(".".join([LOG_PREFIX, name]))
    return logger


def set_app_log_level(level):
    logger = getLogger(LOG_PREFIX)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
