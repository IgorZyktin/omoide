"""Repository that performs operations on items."""
import abc
from typing import Collection
from uuid import UUID

from omoide import domain
from omoide import models


class AbsItemsRepo(abc.ABC):
    """Repository that performs operations on items."""

    @abc.abstractmethod
    async def check_access(
        self,
        user: models.User,
        uuid: UUID,
    ) -> models.AccessStatus:
        """Check access to the Item with given UUID for the given User."""

    @abc.abstractmethod
    async def get_root_item(self, user: models.User) -> models.Item:
        """Return root Item for given user."""

    @abc.abstractmethod
    async def get_all_root_items(
        self,
        *users: models.User,
    ) -> list[models.Item]:
        """Return list of root items."""

    # TODO - remove this method
    @abc.abstractmethod
    async def read_item(
        self,
        uuid: UUID,
    ) -> domain.Item | None:
        """Return Item or None."""

    @abc.abstractmethod
    async def get_item(self, uuid: UUID) -> models.Item:
        """Return Item."""

    @abc.abstractmethod
    async def get_items_anon(
        self,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> list[models.Item]:
        """Return Items."""

    @abc.abstractmethod
    async def get_items_known(
        self,
        user: models.User,
        owner_uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str | None,
        limit: int,
    ) -> list[models.Item]:
        """Return Items."""

    @abc.abstractmethod
    async def count_items_by_owner(
        self,
        user: models.User,
        collections: bool = False,
    ) -> int:
        """Return total amount of items for given user uuid."""

    @abc.abstractmethod
    async def count_all_children_of(
        self,
        item: domain.Item,
    ) -> int:
        """Count dependant items."""

    @abc.abstractmethod
    async def get_children(self, item: models.Item, ) -> list[models.Item]:
        """Return all direct descendants of the given item."""

    @abc.abstractmethod
    async def get_parents(self, item: models.Item) -> list[models.Item]:
        """Return lineage of all parents for the given item."""

    @abc.abstractmethod
    async def get_siblings(self, item: models) -> list[models.Item]:
        """Return all siblings for the given item."""

    @abc.abstractmethod
    async def get_direct_children_uuids_of(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> list[UUID]:
        """Return all direct items of th given item."""

    @abc.abstractmethod
    async def read_computed_tags(
        self,
        uuid: UUID,
    ) -> list[str]:
        """Return all computed tags for the item."""

    @abc.abstractmethod
    async def read_item_by_name(
        self,
        user: models.User,
        name: str,
    ) -> domain.Item | None:
        """Return corresponding item."""

    @abc.abstractmethod
    async def get_free_uuid(self) -> UUID:
        """Generate new UUID for the item."""

    @abc.abstractmethod
    async def create_item(self, item: models.Item) -> None:
        """Return id for created item."""

    @abc.abstractmethod
    async def update_item(
        self,
        item: domain.Item,
    ) -> None:
        """Update existing item."""

    @abc.abstractmethod
    async def delete_item(self, item: models.Item) -> None:
        """Delete item."""

    @abc.abstractmethod
    async def check_child(
        self,
        possible_parent_uuid: UUID,
        possible_child_uuid: UUID,
    ) -> bool:
        """Return True if given item is actually a child."""

    @abc.abstractmethod
    async def update_permissions(
        self,
        uuid: UUID,
        override: bool,
        added: Collection[UUID],
        deleted: Collection[UUID],
        all_permissions: Collection[UUID],
    ) -> None:
        """Apply new permissions for given item UUID."""

    @abc.abstractmethod
    async def add_tags(
        self,
        uuid: UUID,
        tags: Collection[str],
    ) -> None:
        """Add new tags to computed tags of the item."""

    @abc.abstractmethod
    async def delete_tags(
        self,
        uuid: UUID,
        tags: Collection[str],
    ) -> None:
        """Remove tags from computed tags of the item."""

    @abc.abstractmethod
    async def add_permissions(
        self,
        uuid: UUID,
        permissions: Collection[UUID],
    ) -> None:
        """Add new users to computed permissions of the item."""

    @abc.abstractmethod
    async def delete_permissions(
        self,
        uuid: UUID,
        permissions: Collection[UUID],
    ) -> None:
        """Remove users from computed permissions of the item."""
