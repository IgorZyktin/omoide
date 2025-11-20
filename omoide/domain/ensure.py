"""Permission checking utils."""

from omoide import exceptions
from omoide import models


def registered(user: models.User, error_message: str) -> None:
    """Raise if user is Anon."""
    if user.is_not_anon:
        return

    raise exceptions.AccessDeniedError(error_message)


def owner(user: models.User, item: models.Item, error_message: str) -> None:
    """Raise if user is not owner."""
    if user.is_admin or item.owner_id == user.id:
        return

    raise exceptions.AccessDeniedError(error_message)


def can_see(user: models.User, item: models.Item, error_message: str) -> None:
    """Raise if user cannot see this."""
    if user.is_admin or item.owner_id == user.id or user.id in item.permissions:
        return

    raise exceptions.AccessDeniedError(error_message)
