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
        who_asking: models.User,
        target: str = '',
        override: str = '',
    ) -> None:
        """Raise if Anon requesting this."""
        if who_asking.is_anon:
            if override:
                msg = override
            elif target:
                msg = f'Anonymous users are not allowed to {target}'
            else:
                msg = (
                    'Anonymous users are not allowed to perform such requests'
                )

            raise exceptions.AccessDeniedError(msg)

        return None
