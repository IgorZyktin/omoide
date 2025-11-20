"""Repository that performs operations on EXIF data."""

import abc
from typing import Generic
from typing import TypeVar

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsEXIFRepo(Generic[ConnectionT], abc.ABC):
    """Repository that performs operations on EXIF data."""

    @abc.abstractmethod
    async def create(self, conn: ConnectionT, item: models.Item, exif: models.Exif) -> None:
        """Create EXIF record for the given item."""

    @abc.abstractmethod
    async def get_by_item(self, conn: ConnectionT, item: models.Item) -> models.Exif:
        """Return EXIF record for the given item."""

    @abc.abstractmethod
    async def save(self, conn: ConnectionT, item: models.Item, exif: models.Exif) -> None:
        """Update existing EXIF for the given item or create new one."""

    @abc.abstractmethod
    async def delete(self, conn: ConnectionT, item: models.Item) -> None:
        """Delete EXIF record for the given item."""
