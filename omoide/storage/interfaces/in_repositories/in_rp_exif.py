"""Repository that perform CRUD operations on EXIF records."""
import abc
from uuid import UUID


class AbsEXIFRepository(abc.ABC):
    """Repository that perform CRUD operations on EXIF records."""

    @abc.abstractmethod
    async def create_exif(self, item_uuid: UUID, exif: dict[str, str]) -> None:
        """Create EXIF."""

    @abc.abstractmethod
    async def read_exif(self, item_uuid: UUID) -> dict[str, str]:
        """Return EXIF."""

    @abc.abstractmethod
    async def update_exif(self, item_uuid: UUID, exif: dict[str, str]) -> None:
        """Update EXIF."""

    @abc.abstractmethod
    async def delete_exif(self, item_uuid: UUID) -> None:
        """Delete EXIF."""
