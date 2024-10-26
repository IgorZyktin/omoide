"""Repository that perform CRUD operations on metainfo records."""

import abc
from typing import Any
from uuid import UUID

from omoide import models


class AbsMetainfoRepo(abc.ABC):
    """Repository that perform CRUD operations on metainfo records."""

    @abc.abstractmethod
    async def create_metainfo(self, metainfo: models.Metainfo) -> None:
        """Create metainfo."""

    @abc.abstractmethod
    async def read_metainfo(self, item: models.Item) -> models.Metainfo:
        """Return metainfo."""

    @abc.abstractmethod
    async def get_metainfos(
        self,
        items: list[models.Item],
    ) -> dict[UUID, models.Metainfo | None]:  # TODO use item_id, not UUID
        """Return many metainfo records."""

    @abc.abstractmethod
    async def update_metainfo(
        self,
        user: models.User,
        item_uuid: UUID,
        metainfo: models.Metainfo,
    ) -> None:
        """Update metainfo."""

    @abc.abstractmethod
    async def mark_metainfo_updated(self, item_uuid: UUID) -> None:
        """Set `updated_at` field to current datetime."""

    @abc.abstractmethod
    async def update_metainfo_extras(
        self,
        item_uuid: UUID,
        new_extras: dict[str, Any],
    ) -> None:
        """Add new data to extras."""

    @abc.abstractmethod
    async def add_item_note(
        self, item: models.Item, key: str, value: str
    ) -> None:
        """Add new note to given item."""

    @abc.abstractmethod
    async def get_total_disk_usage(
        self,
        user: models.User,
    ) -> models.DiskUsage:
        """Return total disk usage for specified user."""
