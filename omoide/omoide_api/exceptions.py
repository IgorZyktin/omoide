"""API-level exceptions."""
from typing import Any


class BaseOmoideApiError(Exception):
    """Base class for all API exception."""

    def __init__(
            self,
            msg: str,
            **kwargs: Any,
    ) -> None:
        """Initialize instance."""
        super().__init__(msg)
        self.msg = msg
        self.kwargs = kwargs
        self.rendered_text = msg

        if kwargs:
            self.rendered_text = self.rendered_text.format(**kwargs)

    def __str__(self) -> str:
        """Return textual representation."""
        return self.rendered_text

    def __repr__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return f'{name}({self.msg!r}, {self.kwargs})'


class DoesNotExistError(BaseOmoideApiError):
    """Target resource does not exist."""


class RestrictedError(BaseOmoideApiError):
    """User has no rights to do this."""


class InvalidInputError(BaseOmoideApiError):
    """User sent us something strange."""
