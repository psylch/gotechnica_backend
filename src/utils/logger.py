import logging
from typing import Optional

from src.config import get_settings

LOG_FORMAT = "%(levelname)s | %(asctime)s | %(name)s:%(lineno)d | %(message)s"


def configure_logging() -> None:
    """Configure root logging according to settings only once."""
    settings = get_settings()
    if not logging.getLogger().handlers:
        logging.basicConfig(level=settings.log_level, format=LOG_FORMAT)
    logging.getLogger("uvicorn.error").setLevel(settings.log_level)
    logging.getLogger("uvicorn.access").setLevel(settings.log_level)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name or "snapopedia")
