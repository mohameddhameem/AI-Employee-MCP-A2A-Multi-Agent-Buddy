"""
Centralized logging configuration for A2A Multi-Agent project.
"""
import logging
from logging import StreamHandler, Formatter


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure root logger with a StreamHandler and a standard formatter.

    :param level: Logging level, defaults to logging.INFO.
    """
    handler = StreamHandler()
    formatter = Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Avoid adding duplicate handlers
    if not any(isinstance(h, StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)
