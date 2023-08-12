"""Domain-level exceptions.
"""
from uuid import UUID

from omoide.domain import actions


class BaseOmoideException(Exception):
    """Root-level exception."""

    def __str__(self) -> str:
        """Return textual representation."""
        doc = type(self).__doc__ or ''
        template = doc.rstrip('.')
        return template.format(**self.__dict__)

    def __repr__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        pairs = ', '.join(
            f'{key}={value!r}'
            for key, value in self.__dict__.items()
        )
        return f'{name}({pairs})'


class DoesNotExistError(BaseOmoideException):
    """Target resource does not exist."""


class AlreadyExistError(BaseOmoideException):
    """Target resource already exist."""


class ForbiddenError(BaseOmoideException):
    """User has no rights to do this."""


class CannotModifyItemComponentError(ForbiddenError):
    """You are not allowed to modify components of item {item_uuid}."""

    def __init__(self, item_uuid: UUID) -> None:
        """Initialize instance."""
        self.item_uuid = item_uuid


class UnexpectedActionError(ForbiddenError):
    """No rule for {action}."""

    def __init__(self, action: actions.Action) -> None:
        """Initialize instance."""
        self.action = action


class EXIFAlreadyExistError(AlreadyExistError):
    """EXIF for item {item_uuid} is already exist."""

    def __init__(self, item_uuid: UUID) -> None:
        """Initialize instance."""
        self.item_uuid = item_uuid


class EXIFDoesNotExistError(DoesNotExistError):
    """EXIF for item {item_uuid} does not exist."""

    def __init__(self, item_uuid: UUID) -> None:
        """Initialize instance."""
        self.item_uuid = item_uuid


class ItemDoesNotExistError(DoesNotExistError):
    """Item with {uuid} does not exist."""

    def __init__(self, item_uuid: UUID) -> None:
        """Initialize instance."""
        self.item_uuid = item_uuid
