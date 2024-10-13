"""Project exceptions."""

from typing import Any


class BaseOmoideError(Exception):
    """Base class for all API exception."""

    def __init__(
        self,
        msg: str = '',
        **kwargs: Any,
    ) -> None:
        """Initialize instance."""
        class_ = type(self)
        self.__msg = (msg or class_.__doc__ or '').rstrip('.').strip()
        self.__kwargs = kwargs
        self.__rendered_text = msg
        self.__name = class_.__name__

        if kwargs:
            self.__rendered_text = self.__render_text(self.__msg, **kwargs)

        super().__init__(self.__rendered_text)

    @staticmethod
    def __render_text(template: str, **kwargs: str) -> str:
        """Safely convert error to text message."""
        try:
            rendered_text = template.format(**kwargs)
        except (IndexError, KeyError, ValueError) as exc:
            rendered_text = f'{template} {kwargs} ({exc})'
        return rendered_text

    def __str__(self) -> str:
        """Return textual representation."""
        return self.__rendered_text

    def __repr__(self) -> str:
        """Return textual representation."""
        return f'{self.__name}({self.__msg!r}, {self.__kwargs})'


class DoesNotExistError(BaseOmoideError):
    """Target resource does not exist."""


class AlreadyExistsError(BaseOmoideError):
    """Target resource already exists."""


class AccessDeniedError(BaseOmoideError):
    """User has no rights to do this."""


class InvalidInputError(BaseOmoideError):
    """User sent us something strange."""


class NotAllowedError(BaseOmoideError):
    """User has access to the object, but cannot perform specific operation."""


class UnknownWorkerError(BaseOmoideError):
    """Worker {worker_name} is not in list of registered workers."""


class UnknownSerialOperationError(BaseOmoideError):
    """There is no operation of type {name!r}."""
