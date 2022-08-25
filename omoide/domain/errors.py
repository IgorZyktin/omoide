# -*- coding: utf-8 -*-
"""Custom errors (an alternative to exceptions).
"""
from typing import Any
from typing import Optional


class Error:
    """Custom DTO that holds errors."""
    template: str

    def __init__(
            self,
            *,
            template: Optional[str] = None,
            exception: Optional[Exception] = None,
            **kwargs: Any,
    ) -> None:
        """Initialize instance."""
        self.template = template or self.template
        self.exception = exception
        self.kwargs = kwargs

    def __str__(self) -> str:
        """Return textual representation."""
        message = self.template.format(**self.kwargs)
        if self.exception:
            message += f' [{type(self.exception)}({self.exception})]'
        return message


class UnexpectedAction(Error):
    """Policy was not programmed for this."""
    template = 'No rule for {action}'


class ItemDoesNotExist(Error):
    """Item does not exist or hidden from the user."""
    template = 'Item {uuid} does not exist'


class ItemRequiresAccess(Error):
    """Item exists but user has no permission to modify it."""
    template = 'You are not allowed to interact with item {uuid}'


class EXIFDoesNotExist(Error):
    """EXIF for item does not exist or hidden from the user."""
    template = 'EXIF for item {uuid} does not exist'
