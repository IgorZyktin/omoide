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
    async def create(self, conn: ConnectionT, item: models.Item) -> int:
        """Create new item."""

    @abc.abstractmethod
    async def get_by_id(self, conn: ConnectionT, item_id: int) -> models.Item:
        """Return Item with given id."""

    @abc.abstractmethod
    async def get_by_uuid(self, conn: ConnectionT, uuid: UUID) -> models.Item:
        """Return Item with given UUID."""

    @abc.abstractmethod
    async def get_by_name(self, conn: ConnectionT, name: str) -> models.Item:
        """Return Item with given name."""

    @abc.abstractmethod
    async def get_children(self, conn: ConnectionT, item: models.Item) -> list[models.Item]:
        """Return list of children for given item."""

    @abc.abstractmethod
    async def count_children(self, conn: ConnectionT, item: models.Item) -> int:
        """Count all children of an item with given UUID."""

    @abc.abstractmethod
    async def get_parents(self, conn: ConnectionT, item: models.Item) -> list[models.Item]:
        """Return list of parents for given item."""

    @abc.abstractmethod
    async def get_siblings(self, conn: ConnectionT, item: models.Item) -> list[models.Item]:
        """Return list of siblings for given item."""

    @abc.abstractmethod
    async def get_items_anon(
        self,
        conn: ConnectionT,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> list[models.Item]:
        """Return Items."""

    @abc.abstractmethod
    async def get_items_known(
        self,
        conn: ConnectionT,
        user: models.User,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> list[models.Item]:
        """Return Items."""

    @abc.abstractmethod
    async def check_child(
        self,
        conn: ConnectionT,
        possible_parent_uuid: UUID,
        possible_child_uuid: UUID,
    ) -> bool:
        """Return True if given item is actually a child."""

    @abc.abstractmethod
    async def save(self, conn: ConnectionT, item: models.Item) -> bool:
        """Save the given item."""

    @abc.abstractmethod
    async def delete(self, conn: ConnectionT, item: models.Item) -> bool:
        """Delete the given item."""

    @abc.abstractmethod
    async def read_computed_tags(
        self,
        conn: ConnectionT,
        uuid: UUID,
    ) -> list[str]:
        """Return all computed tags for the item."""

    @abc.abstractmethod
    async def count_all_children_of(
        self,
        conn: ConnectionT,
        item: models.Item,
    ) -> int:
        """Count dependant items."""
