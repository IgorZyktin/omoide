# -*- coding: utf-8 -*-
"""Domain-level exceptions.
"""


class BaseOmoideException(Exception):
    """Root-level exception."""


class IncorrectUUID(BaseOmoideException):
    """Given UUID is not correct."""
