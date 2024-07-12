"""Project exceptions."""
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
        self.name = type(self).__name__

        if kwargs:
            self.rendered_text = self._render_text(msg, **kwargs)

    @staticmethod
    def _render_text(template: str, **kwargs) -> str:
        """Safely convert error to text message."""
        try:
            rendered_text = template.format(**kwargs)
        except (IndexError, KeyError, ValueError) as exc:
            rendered_text = f'{template} {kwargs} ({exc})'
        return rendered_text

    def __str__(self) -> str:
        """Return textual representation."""
        return self.rendered_text

    def __repr__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return f'{name}({self.msg!r}, {self.kwargs})'


class DoesNotExistError(BaseOmoideApiError):
    """Target resource does not exist."""


class AlreadyExistsError(BaseOmoideApiError):
    """Target resource already exists."""


class AccessDeniedError(BaseOmoideApiError):
    """User has no rights to do this."""


class InvalidInputError(BaseOmoideApiError):
    """User sent us something strange."""
