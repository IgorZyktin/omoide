"""Common use case elements."""
import abc

from omoide import exceptions
from omoide import models
from omoide.infra.mediator import Mediator


class BaseAPIUseCase(abc.ABC):
    """Base use case class for API."""

    def __init__(self, mediator: Mediator) -> None:
        """Initialize instance."""
        self.mediator = mediator

    @staticmethod
    def ensure_not_anon(
        user: models.User,
        operation: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if Anon requesting this."""
        if user.is_not_anon:
            return

        if error_message:
            msg = error_message
        elif operation:
            msg = f'Anonymous users are not allowed to {operation}'
        else:
            msg = (
                'Anonymous users are not allowed to perform such requests'
            )

        raise exceptions.AccessDeniedError(msg)

    @staticmethod
    def ensure_admin_or_owner_or_allowed_to(
        user: models.User,
        item: models.Item,
        subject: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if one user tries to manage object of some other user."""
        if any(
            (
                item.owner_uuid == user.uuid,
                str(user.uuid) in item.permissions,
            )
        ) or user.is_admin:
            return

        if error_message:
            msg = error_message
        elif subject:
            msg = (
                'You are not allowed to perform '
                f'such operations with {subject}'
            )
        else:
            msg = 'You are not allowed to perform such operations'

        raise exceptions.AccessDeniedError(msg)

    @staticmethod
    def ensure_admin_or_owner(
        user: models.User,
        target: models.Item | models.User,
        subject: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if one user tries to manage object of some other user."""
        conditions: list[bool] = []

        if isinstance(target, models.User):
            conditions.append(user.uuid == target.uuid)
        else:
            conditions.append(target.owner_uuid == user.uuid)

        if all(conditions) or user.is_admin:
            return

        if error_message:
            msg = error_message
        elif subject:
            msg = (
                'You are not allowed to perform '
                f'such operations with {subject}'
            )
        else:
            msg = 'You are not allowed to perform such operations'

        raise exceptions.AccessDeniedError(msg)

    @staticmethod
    def ensure_admin_or_allowed_to(
        user: models.User,
        item: models.Item,
        subject: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if one user tries to manage object of some other user."""
        if all(
            (
                item.owner_uuid == user.uuid,
                str(user.uuid) in item.permissions
            )
        ) or user.is_admin:
            return

        if error_message:
            msg = error_message
        elif subject:
            msg = (
                'You are not allowed to perform '
                f'such operations with {subject}'
            )
        else:
            msg = 'You are not allowed to perform such operations'

        raise exceptions.AccessDeniedError(msg)

    @staticmethod
    def ensure_admin(
        user: models.User,
        subject: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if user is not admin."""
        if user.is_admin:
            return

        if error_message:
            msg = error_message
        elif subject:
            msg = (
                'You are not allowed to perform '
                f'such operations with {subject}'
            )
        else:
            msg = 'You are not allowed to perform such operations'

        raise exceptions.AccessDeniedError(msg)
