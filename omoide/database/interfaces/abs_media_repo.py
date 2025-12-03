"""Repository that perform CRUD operations on media records."""

import abc
from datetime import datetime
from typing import Generic
from typing import TypeVar

from omoide import const
from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsMediaRepo(abc.ABC, Generic[ConnectionT]):
    """Repository that perform CRUD operations on media records."""

    @abc.abstractmethod
    async def create_media(self, conn: ConnectionT, media: models.Media) -> int:
        """Create Media, return media id."""

    @abc.abstractmethod
    async def delete_processed_media(self, conn: ConnectionT, user: models.User) -> int:
        """Delete fully downloaded media rows."""

    @abc.abstractmethod
    async def delete_all_processed_media(self, conn: ConnectionT) -> int:
        """Delete fully downloaded media rows."""

    @abc.abstractmethod
    async def copy_image(
        self,
        conn: ConnectionT,
        source_item: models.Item,
        target_item: models.Item,
        media_type: const.MEDIA_TYPE,
        ext: str,
        moment: datetime,
    ) -> int:
        """Save intention to copy data between items."""
