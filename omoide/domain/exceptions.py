# -*- coding: utf-8 -*-
"""Domain-level exceptions.
"""


class BaseOmoideException(Exception):
    """Root-level exception."""


class IncorrectUUID(BaseOmoideException):
    """Given UUID is not correct."""


class NotFound(BaseOmoideException):
    """Target resource does not exist."""


class Unauthorized(BaseOmoideException):
    """User must be logged in to get this resource."""


class Forbidden(BaseOmoideException):
    """User has no access to this resource."""
