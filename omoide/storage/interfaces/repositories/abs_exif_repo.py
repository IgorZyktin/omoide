"""Repository that performs CRUD operations on EXIF records."""

import abc
from typing import Any

from omoide import models


class AbsEXIFRepository(abc.ABC):
    """Repository that performs CRUD operations on EXIF records."""

    @abc.abstractmethod
    async def create_exif(
        self,
        item: models.Item,
        exif: dict[str, Any],
    ) -> None:
        """Create EXIF for given item."""

    @abc.abstractmethod
    async def read_exif(self, item: models.Item) -> dict[str, Any]:
        """Return EXIF for given item."""

    @abc.abstractmethod
    async def update_exif(
        self,
        item: models.Item,
        exif: dict[str, Any],
    ) -> None:
        """Update EXIF for given item."""

    @abc.abstractmethod
    async def delete_exif(self, item: models.Item) -> None:
        """Delete EXIF for given item."""
