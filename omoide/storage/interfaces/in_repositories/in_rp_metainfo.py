"""Repository that perform CRUD operations on metainfo records."""
import abc
from uuid import UUID

from omoide import models


class AbsMetainfoRepo(abc.ABC):
    """Repository that perform CRUD operations on metainfo records."""

    @abc.abstractmethod
    async def create_empty_metainfo(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> None:
        """Create metainfo with blank fields."""

    @abc.abstractmethod
    async def read_metainfo(self, item_uuid: UUID) -> models.Metainfo:
        """Return metainfo."""

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
        uuid: UUID,
        new_extras: dict[str, None | int | float | str | bool],
    ) -> None:
        """Add new data to extras."""
