"""Repository that perform CRUD operations on media records."""

import abc
from datetime import datetime

from omoide import const
from omoide import models


class AbsMediaRepo(abc.ABC):
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
        source_item: models.Item,
        target_item: models.Item,
        media_type: const.MEDIA_TYPE,
        ext: str,
        moment: datetime,
    ) -> int:
        """Save intention to copy data between items."""

    @abc.abstractmethod
    async def mark_file_as_orphan(
        self,
        item: models.Item,
        media_type: const.MEDIA_TYPE,
        ext: str,
        moment: datetime,
    ) -> None:
        """Mark corresponding files as useless."""
