"""Repository that perform operations on items."""

import abc
from typing import Generic
from typing import TypeVar
from uuid import UUID

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsItemsRepo(Generic[ConnectionT], abc.ABC):
    """Repository that perform operations on items."""

    @abc.abstractmethod
    def get_by_id(self, conn: ConnectionT, item_id: int) -> models.Item:
        """Return Item with given id."""

    @abc.abstractmethod
    def get_by_uuid(self, conn: ConnectionT, uuid: UUID) -> models.Item:
        """Return Item with given UUID."""

    @abc.abstractmethod
    def get_children(
        self,
        conn: ConnectionT,
        item: models.Item,
    ) -> list[models.Item]:
        """Return children of given item."""

    @abc.abstractmethod
    def get_parents(
        self,
        conn: ConnectionT,
        item: models.Item,
    ) -> list[models.Item]:
        """Return parents of given item."""

    @abc.abstractmethod
    def save(self, conn: ConnectionT, item: models.Item) -> None:
        """Save given item."""
