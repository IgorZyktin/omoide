"""Repository that performs operations on items."""

import abc
from collections.abc import Collection
from uuid import UUID

from omoide import models


class AbsItemsRepo(abc.ABC):
    """Repository that performs operations on items."""

    # TODO - remove this method
    @abc.abstractmethod
    async def read_item(
        self,
        uuid: UUID,
    ) -> models.Item | None:
        """Return Item or None."""

    @abc.abstractmethod
    async def get_item(self, uuid: UUID) -> models.Item:
        """Return Item."""

    @abc.abstractmethod
    async def get_children(self, item: models.Item) -> list[models.Item]:
        """Return all direct descendants of the given item."""

    @abc.abstractmethod
    async def get_parents(self, item: models.Item) -> list[models.Item]:
        """Return lineage of all parents for the given item."""

    @abc.abstractmethod
    async def create_item(self, item: models.Item) -> None:
        """Return id for created item."""

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
