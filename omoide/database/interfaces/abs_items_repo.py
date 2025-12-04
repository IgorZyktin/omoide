"""Repository that perform operations on items."""

import abc
from collections.abc import Collection
from typing import Generic
from typing import TypeVar
from uuid import UUID

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsItemsRepo(abc.ABC, Generic[ConnectionT]):
    """Repository that perform operations on items."""

    @abc.abstractmethod
    async def create(self, conn: ConnectionT, item: models.Item) -> int:
        """Create new item."""

    @abc.abstractmethod
    async def get_by_id(
        self,
        conn: ConnectionT,
        item_id: int,
        read_deleted: bool = False,
    ) -> models.Item:
        """Return Item with given id."""

    @abc.abstractmethod
    async def get_by_uuid(
        self,
        conn: ConnectionT,
        uuid: UUID,
        read_deleted: bool = False,
    ) -> models.Item:
        """Return Item with given UUID."""

    @abc.abstractmethod
    async def get_by_name(
        self,
        conn: ConnectionT,
        name: str,
        read_deleted: bool = False,
    ) -> models.Item:
        """Return Item with given name."""

    @abc.abstractmethod
    async def get_children(
        self,
        conn: ConnectionT,
        item: models.Item,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[models.Item]:
        """Return list of children for given item."""

    @abc.abstractmethod
    async def count_children(self, conn: ConnectionT, item: models.Item) -> int:
        """Count all children of an item with given UUID."""

    @abc.abstractmethod
    async def get_parents(self, conn: ConnectionT, item: models.Item) -> list[models.Item]:
        """Return list of parents for given item."""

    @abc.abstractmethod
    async def get_siblings(
        self,
        conn: ConnectionT,
        item: models.Item,
        collections: bool | None = None,
    ) -> list[models.Item]:
        """Return list of siblings for given item."""

    @abc.abstractmethod
    async def get_family(self, conn: ConnectionT, item: models.Item) -> list[models.Item]:
        """Return list of all descendants for given item (including item itself)."""

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
    async def is_child(
        self,
        conn: ConnectionT,
        parent: models.Item,
        child: models.Item,
    ) -> bool:
        """Return True if given item is a child of given parent."""

    @abc.abstractmethod
    async def save(self, conn: ConnectionT, item: models.Item) -> bool:
        """Save the given item."""

    @abc.abstractmethod
    async def soft_delete(self, conn: ConnectionT, item: models.Item) -> bool:
        """Mark tem as deleted."""

    @abc.abstractmethod
    async def delete(self, conn: ConnectionT, item: models.Item) -> bool:
        """Delete the given item."""

    @abc.abstractmethod
    async def read_computed_tags(self, conn: ConnectionT, item: models.Item) -> list[str]:
        """Return all computed tags for the item."""

    @abc.abstractmethod
    async def count_family(self, conn: ConnectionT, item: models.Item) -> int:
        """Count all descendants for given item (including the item itself)."""

    @abc.abstractmethod
    async def get_parent_names(
        self,
        conn: ConnectionT,
        items: Collection[models.Item],
    ) -> dict[int, str | None]:
        """Get names of parents of the given items."""

    @abc.abstractmethod
    async def get_batch(
        self,
        conn: ConnectionT,
        only_users: Collection[int],
        only_items: Collection[int],
        batch_size: int,
        last_seen: int | None,
        limit: int | None,
    ) -> list[models.Item]:
        """Iterate on all items."""

    @abc.abstractmethod
    async def cast_uuids(self, conn: ConnectionT, uuids: Collection[UUID]) -> set[int]:
        """Convert collection of `item_uuid` into set of `item_id`."""

    @abc.abstractmethod
    async def get_map(
        self,
        conn: ConnectionT,
        ids: Collection[int],
    ) -> dict[int, models.Item | None]:
        """Get map of items."""

    @abc.abstractmethod
    async def get_duplicates(
        self,
        conn: ConnectionT,
        user: models.User,
        item: models.Item | None,
        limit: int,
    ) -> list[models.Duplicate]:
        """Return groups of items with same hash."""
