"""Repository that performs operations on items."""
import abc
import datetime
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
    ) -> list[domain.Item]:
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

    # TODO - change naming
    @abc.abstractmethod
    async def get_children_(
        self,
        item: domain.Item,
    ) -> list[models.Item]:
        """Return all direct descendants of the given item."""

    @abc.abstractmethod
    async def read_children_of(
        self,
        user: models.User,
        item: domain.Item,
        ignore_collections: bool,
    ) -> list[domain.Item]:
        """Return all direct descendants of the given item."""

    @abc.abstractmethod
    async def get_simple_location(
        self,
        user: models.User,
        owner: models.User,
        item: domain.Item,
    ) -> domain.SimpleLocation | None:
        """Return Location of the item (without pagination)."""

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
    async def get_all_parents(
        self,
        user: models.User,
        item: domain.Item,
    ) -> list[domain.Item]:
        """Return all parents of the given item."""

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
    async def create_item(
        self,
        user: models.User,
        item: domain.Item,
    ) -> domain.Item:
        """Return UUID for created item."""

    @abc.abstractmethod
    async def update_item(
        self,
        item: domain.Item,
    ) -> None:
        """Update existing item."""

    @abc.abstractmethod
    async def mark_files_as_orphans(
        self,
        item: domain.Item,
        moment: datetime.datetime,
    ) -> None:
        """Mark corresponding files as useless."""

    @abc.abstractmethod
    async def delete_item(
        self,
        item_uuid: UUID,
    ) -> None:
        """Delete item with given UUID."""

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
