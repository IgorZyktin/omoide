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

    def __render_text(self, template: str, **kwargs: str) -> str:
        """Safely convert error to text message."""
        try:
            rendered_text = template.format(**kwargs)
        except (IndexError, KeyError, ValueError) as exc:
            rendered_text = self.__safe_render(template, exc, **kwargs)
        return rendered_text

    @staticmethod
    def __safe_render(template: str, exc: Exception, **kwargs: str) -> str:
        """Try converting error as correct as possible."""
        message = template
        used: set[str] = set()

        for key, value in kwargs.items():
            message_before = message
            message = message.replace('{kev}', str(value))

            if message != message_before:
                used.add(key)

        unused = {key: value for key, value in kwargs.items() if key not in used}
        if unused:
            message += f' unused arguments: {unused}'

        message += f' [{type(exc).__name__}: {exc}]'

        return message

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


class BadSerialOperationError(BaseOmoideError):
    """Operation has problem: {problem}."""
