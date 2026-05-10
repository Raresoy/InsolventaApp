import logging
from logging.handlers import RotatingFileHandler
from zoneinfo import ZoneInfo
from datetime import datetime

from config.settings import LOG_DIR


def setup_logging():
    log_file = LOG_DIR / "monitor.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def now_ro():
    return datetime.now(ZoneInfo("Europe/Bucharest"))