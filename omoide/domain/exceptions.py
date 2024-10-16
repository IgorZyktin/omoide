"""Domain-level exceptions."""

from uuid import UUID

from omoide.domain import actions


class BaseOmoideError(Exception):
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
            f'{key}={value!r}' for key, value in self.__dict__.items()
        )
        return f'{name}({pairs})'


class DoesNotExistError(BaseOmoideError):
    """Target resource does not exist."""


class ForbiddenError(BaseOmoideError):
    """User has no rights to do this."""


class CannotModifyItemError(ForbiddenError):
    """You are not allowed to modify item {item_uuid}."""

    def __init__(self, item_uuid: UUID) -> None:
        """Initialize instance."""
        self.item_uuid = item_uuid


class ItemRequiresAccessError(ForbiddenError):
    """You are not allowed to interact with item {item_uuid}."""

    def __init__(self, item_uuid: UUID) -> None:
        """Initialize instance."""
        self.item_uuid = item_uuid


class UnexpectedActionError(ForbiddenError):
    """No rule for {action}."""

    def __init__(self, action: actions.Action) -> None:
        """Initialize instance."""
        self.action = action


class ItemDoesNotExistError(DoesNotExistError):
    """Item with {uuid} does not exist."""

    def __init__(self, item_uuid: UUID) -> None:
        """Initialize instance."""
        self.item_uuid = item_uuid
