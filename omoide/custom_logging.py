"""Logging tools."""

import sys
from typing import TypeAlias

import loguru

Logger: TypeAlias = 'loguru.Logger'


def init_logging(level: str, diagnose: bool) -> None:
    """Configure logger."""
    loguru.logger.remove()

    if level != 'NOTSET':
        loguru.logger.add(sys.stderr, level=level, diagnose=diagnose)


def get_logger(name: str) -> Logger:
    """Return configured logger instance."""
    _ = name  # to be able to switch to the default logger
    return loguru.logger
