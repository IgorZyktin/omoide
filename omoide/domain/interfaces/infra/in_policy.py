"""Interface for access policy.
"""
import abc
from uuid import UUID

from omoide import models
from omoide.domain import actions
from omoide.domain.errors import Error
from omoide.storage import interfaces

__all__ = [
    'AbsPolicy',
]


class AbsPolicy(abc.ABC):
    """Abstract policy checker."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsRepo,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo

    @abc.abstractmethod
    async def is_restricted(
            self,
            user: models.User,
            uuid: UUID | None,
            action: actions.Action,
    ) -> Error | None:
        """Return Error if action is not permitted."""

    @abc.abstractmethod
    async def check(
            self,
            user: models.User,
            uuid: UUID,  # FIXME - add None as a variant
            action: actions.Action,
    ) -> None:
        """Raise if action is not permitted."""
