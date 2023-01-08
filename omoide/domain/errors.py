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


class EXIFDoesNotExist(Error):
    """EXIF for item does not exist."""
    template = 'EXIF for item {uuid} does not exist'


class UserDoesNotExist(Error):
    """User with uuid does not exist."""
    template = 'User {uuid} does not exist'


class MediaDoesNotExist(Error):
    """Media does not exist."""
    template = 'Media with id {id} for item {uuid} does not exist'


class MetainfoDoesNotExist(Error):
    """Metainfo for item does not exist."""
    template = 'Metainfo for item {uuid} does not exist'


class AuthenticationRequired(Error):
    """User must log in."""
    template = 'You must be logged in to do this'
