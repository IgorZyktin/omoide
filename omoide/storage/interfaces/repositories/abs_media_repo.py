"""Repository that perform CRUD operations on media records."""
import abc
from uuid import UUID

from omoide import models


class AbsMediaRepository(abc.ABC):
    """Repository that perform CRUD operations on media records."""

    @abc.abstractmethod
    async def create_media(self, media: models.Media) -> int:
        """Create Media, return media id."""

    @abc.abstractmethod
    async def delete_processed_media(self, user: models.User) -> int:
        """Delete fully downloaded media rows."""

    @abc.abstractmethod
    async def delete_all_processed_media(self) -> int:
        """Delete fully downloaded media rows."""

    @abc.abstractmethod
    async def copy_image(
        self,
        owner_uuid: UUID,
        source_uuid: UUID,
        target_uuid: UUID,
        media_type: str,
        ext: str,
    ) -> int:
        """Save intention to copy data between items."""
