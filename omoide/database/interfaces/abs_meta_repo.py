"""Repository that perform CRUD operations on metainfo records."""

import abc
from typing import Generic
from typing import TypeVar
from uuid import UUID

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
    async def get_metainfos(
        self,
        conn: ConnectionT,
        items: list[models.Item],
    ) -> dict[UUID, models.Metainfo | None]:  # TODO use item_id, not UUID
        """Return many metainfo records."""

    @abc.abstractmethod
    async def update_metainfo(
        self,
        conn: ConnectionT,
        item_uuid: UUID,
        metainfo: models.Metainfo,
    ) -> None:
        """Update metainfo."""

    @abc.abstractmethod
    async def mark_metainfo_updated(self, conn: ConnectionT, item_uuid: UUID) -> None:
        """Set `updated_at` field to current datetime."""

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
    async def get_total_disk_usage(
        self,
        conn: ConnectionT,
        user: models.User,
    ) -> models.DiskUsage:
        """Return total disk usage for specified user."""
