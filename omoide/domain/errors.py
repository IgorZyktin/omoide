"""Custom errors (an alternative to exceptions).
"""
from functools import cached_property
from typing import Any
from typing import Optional


# TODO - find a way to make formatting attributes required


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


class InvalidUUID(Error):
    """User gave us bad UUID."""
    template = 'Invalid UUID: {uuid!r}'


class UnexpectedAction(Error):
    """Policy was not programmed for this."""
    template = 'No rule for {action}'


class ItemDoesNotExist(Error):
    """Item does not exist or hidden from the user."""
    template = 'Item {uuid} does not exist'


class ItemHasNoThumbnail(Error):
    """Item has no thumbnail."""
    template = 'Item {uuid} has no thumbnail to copy'


class ItemHasNoPreview(Error):
    """Item has no preview."""
    template = 'Item {uuid} has no preview to copy'


class ItemHasNoContent(Error):
    """Item has no preview."""
    template = 'Item {uuid} has no content to copy'


class ItemRequiresAccess(Error):
    """Item exists but user has no permission to modify it."""
    template = 'You are not allowed to interact with item {uuid}'


class ItemNoDeleteForRoot(Error):
    """User tries to delete root level item."""
    template = 'Top level item {uuid} cannot be deleted'


class ItemModificationByAnon(Error):
    """Anon user tries to modify item."""
    template = 'Anonymous users are not allowed to modify items'


class ItemWrongParent(Error):
    """User tries to set item as a parent to itself or something like that."""
    template = 'Item {new_parent_uuid} cannot be used as a parent for {uuid}'


class ItemItself(Error):
    """User tries to set item as a parent to itself or something like that."""
    template = 'Item {uuid} cannot be a target to itself'


class ItemIsInconsistent(Error):
    """Item has discrepancy, like having content ext but no preview ext."""
    template = 'Item {uuid} is not consistent {message}'


class UserDoesNotExist(Error):
    """User with uuid does not exist."""
    template = 'User {uuid} does not exist'


class MetainfoDoesNotExist(Error):
    """Metainfo for item does not exist."""
    template = 'Metainfo for item {uuid} does not exist'


class AuthenticationRequired(Error):
    """User must log in."""
    template = 'You must be logged in to do this'


class DatabaseError(Error):
    """Failed to perform operation in the DB."""
    template = 'Failed to perform operation'


# -----------------------------------------------------------------------------

class DoesNotExist(Error):
    """Base class that shows that object does not exist."""


class MediaDoesNotExist(DoesNotExist):
    """Does not exist."""
    template = 'Media with id {media_id} does not exist'

    def __init__(self, media_id: int) -> None:
        """Initialize instance."""
        super().__init__()
        self.media_id = media_id
