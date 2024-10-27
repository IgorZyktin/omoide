"""Repository that perform operations on EXIF data."""

import abc
from typing import Any
from typing import Generic
from typing import TypeVar

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsEXIFRepo(Generic[ConnectionT], abc.ABC):
    """Repository that perform operations on EXIF data."""

    @abc.abstractmethod
    async def create(
        self,
        conn: ConnectionT,
        item: models.Item,
        exif: dict[str, Any],
    ) -> None:
        """Create EXIF record for given item."""

    @abc.abstractmethod
    async def get_by_item(
        self,
        conn: ConnectionT,
        item: models.Item,
    ) -> dict[str, Any]:
        """Return EXIF record for given item."""

    @abc.abstractmethod
    async def save(
        self,
        conn: ConnectionT,
        item: models.Item,
        exif: dict[str, Any],
    ) -> bool:
        """Update existing EXIF record for given item or create new one."""

    @abc.abstractmethod
    async def delete(
        self,
        conn: ConnectionT,
        item: models.Item,
    ) -> None:
        """Delete EXIF record for given item."""
