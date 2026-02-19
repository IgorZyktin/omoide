"""Logging tools."""

import sys
from typing import TypeAlias

import loguru

Logger: TypeAlias = 'loguru.Logger'


def init_logging(level: str, diagnose: bool, path: str, rotation: str) -> None:
    """Configure logger."""
    loguru.logger.remove()

    if level != 'NOTSET':
        loguru.logger.add(sys.stderr, level=level, diagnose=diagnose)

    if path:
        loguru.logger.add(path, rotation=rotation)


def get_logger(name: str) -> Logger:
    """Return configured logger instance."""
    _ = name  # to be able to switch to the default logger
    return loguru.logger


def capture_exception_output(title: str) -> str | None:
    """Capture traceback from Loguru."""
    storage = []
    sink_id = loguru.logger.add(sink=lambda msg: storage.append(msg))
    loguru.logger.exception(title)
    loguru.logger.remove(sink_id)
    return storage[0] if storage else None
