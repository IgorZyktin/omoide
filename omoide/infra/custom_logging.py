# -*- coding: utf-8 -*-
"""Logging tools.
"""
import logging
import sys

from loguru import logger


def init_logging(level: str) -> None:
    """Configure logger."""
    logger.remove()

    if level != 'NOTSET':
        logger.add(sys.stderr, level=level)


def get_logger(name: str) -> logging.Logger:
    """Return configured logger instance."""
    _ = name  # to be able to switch to the default logger
    return logger
