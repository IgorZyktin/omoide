"""Common use case elements."""
import abc

from omoide import domain
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
        if user.is_anon:
            if error_message:
                msg = error_message
            elif operation:
                msg = f'Anonymous users are not allowed to {operation}'
            else:
                msg = (
                    'Anonymous users are not allowed to perform such requests'
                )

            raise exceptions.AccessDeniedError(msg)

        return None

    @staticmethod
    def ensure_admin_or_owner(
        user: models.User,
        item: domain.Item,
        subject: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if one user tries to manage object of some other user."""
        if item.owner_uuid != user.uuid and not user.is_admin:
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
        item: domain.Item,
        subject: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if one user tries to manage object of some other user."""
        if (
            item.owner_uuid != user.uuid
            and not user.is_admin
            and str(user.uuid) not in item.permissions
        ):
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
