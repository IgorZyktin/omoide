"""Custom errors (an alternative to exceptions).
"""
from functools import cached_property
from typing import Any
from typing import Optional


class Error:
    """Custom DTO that holds errors."""
    template: str = ''

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

    @cached_property
    def message(self) -> str:
        """Render error message."""
        return self.template.format(**self.kwargs)

    def __str__(self) -> str:
        """Return textual representation."""
        message = self.message
        if self.exception:
            message += f' [{type(self.exception)}({self.exception})]'
        return message

    def __repr__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return f'<{name}({self.message})>'


class NoUUID(Error):
    """User has to give UUID but opted out it."""
    template = 'No UUID specified for the action {name}'


class UnexpectedAction(Error):
    """Policy was not programmed for this."""
    template = 'No rule for {action}'


class ItemDoesNotExist(Error):
    """Item does not exist or hidden from the user."""
    template = 'Item {uuid} does not exist'


class ItemRequiresAccess(Error):
    """Item exists but user has no permission to modify it."""
    template = 'You are not allowed to interact with item {uuid}'


class ItemModificationByAnon(Error):
    """Anon user tries to modify item."""
    template = 'Anonymous users are not allowed to modify items'


class ItemWrongParent(Error):
    """User tries to set item as a parent to itself or something like that."""
    template = 'Item {new_parent_uuid} cannot be used as a parent for {uuid}'
