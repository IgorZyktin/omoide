"""Repository that performs CRUD operations on EXIF records."""

import abc
from typing import Any
from uuid import UUID


class AbsEXIFRepository(abc.ABC):
    """Repository that performs CRUD operations on EXIF records."""

    @abc.abstractmethod
    async def create_exif(self, item_uuid: UUID, exif: dict[str, Any]) -> None:
        """Create EXIF."""

    @abc.abstractmethod
    async def read_exif(self, item_uuid: UUID) -> dict[str, Any]:
        """Return EXIF."""

    @abc.abstractmethod
    async def update_exif(self, item_uuid: UUID, exif: dict[str, Any]) -> None:
        """Update EXIF."""

    @abc.abstractmethod
    async def delete_exif(self, item_uuid: UUID) -> None:
        """Delete EXIF."""
