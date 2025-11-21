"""Policy variants."""

from omoide import exceptions
from omoide import models
from omoide.infra.interfaces import AbsPolicy


class Policy(AbsPolicy):
    """Special class that checks permissions."""

    @staticmethod
    def ensure_registered(user: models.User, to: str, error_message: str | None = None) -> None:
        """Raise if user is anon."""
        if user.is_not_anon:
            return

        if error_message is not None:
            msg = error_message
        else:
            msg = f'Anonymous users are not allowed to {to}'

        raise exceptions.AccessDeniedError(msg)

    @staticmethod
    def ensure_owner(
        user: models.User,
        item: models.Item,
        to: str,
        error_message: str | None = None,
    ) -> None:
        """Continue execution only if user owns given item (or is admin)."""
        if user.is_admin or item.owner_id == user.id:
            return

        if error_message is None:
            msg = f'You are not allowed to {to} for the item {item.uuid}'
        else:
            msg = error_message

        raise exceptions.NotAllowedError(msg)
