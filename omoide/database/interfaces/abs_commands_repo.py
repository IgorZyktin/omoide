"""Repository that perform operations on commands."""

import abc
from typing import Generic
from typing import TypeVar

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsCommandsRepo(abc.ABC, Generic[ConnectionT]):
    """Repository that perform operations on commands."""

    @abc.abstractmethod
    async def soft_delete(
        self,
        conn: ConnectionT,
        requested_by: models.User,
        item: models.Item,
    ) -> int:
        """Soft delete an item."""

    @abc.abstractmethod
    async def hard_delete(
        self,
        conn: ConnectionT,
        requested_by: models.User,
        item: models.Item,
    ) -> int:
        """Hard delete an item."""
