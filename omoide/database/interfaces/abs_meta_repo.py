"""Repository that perform CRUD operations on metainfo records."""

import abc
from collections.abc import Collection
from typing import Generic
from typing import TypeVar

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsMetaRepo(Generic[ConnectionT], abc.ABC):
    """Repository that perform CRUD operations on metainfo records."""

    @abc.abstractmethod
    async def create(self, conn: ConnectionT, metainfo: models.Metainfo) -> None:
        """Create metainfo."""

    @abc.abstractmethod
    async def get_by_item(self, conn: ConnectionT, item: models.Item) -> models.Metainfo:
        """Return metainfo."""

    @abc.abstractmethod
    async def get_metainfo_map(
        self,
        conn: ConnectionT,
        items: Collection[models.Item],
    ) -> dict[int, models.Metainfo | None]:
        """Get map of metainfo records."""

    @abc.abstractmethod
    async def save(self, conn: ConnectionT, metainfo: models.Metainfo) -> None:
        """Update metainfo."""

    @abc.abstractmethod
    async def soft_delete(self, conn: ConnectionT, metainfo: models.Metainfo) -> int:
        """Mark item deleted."""

    @abc.abstractmethod
    async def add_item_note(
        self,
        conn: ConnectionT,
        item: models.Item,
        key: str,
        value: str,
    ) -> None:
        """Add new note to given item."""

    @abc.abstractmethod
    async def get_item_notes(self, conn: ConnectionT, item: models.Item) -> dict[str, str]:
        """Return notes for given item."""

    @abc.abstractmethod
    async def get_total_disk_usage(
        self,
        conn: ConnectionT,
        user: models.User,
    ) -> models.DiskUsage:
        """Return total disk usage for specified user."""
