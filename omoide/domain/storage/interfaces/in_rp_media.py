"""Repository that perform CRUD operations on media records.
"""
import abc
from uuid import UUID

from omoide.domain import errors
from omoide.domain.core import core_models
from omoide.domain.storage.interfaces.in_rp_base import AbsBaseRepository


class AbsMediaRepository(AbsBaseRepository):
    """Repository that perform CRUD operations on media records."""

    @abc.abstractmethod
    async def create_media(
            self,
            media: core_models.Media,
    ) -> core_models.Media | errors.Error:
        """Create Media, return media id."""

    @abc.abstractmethod
    async def get_media_by_id(
            self,
            media_id: int,
    ) -> core_models.Media | errors.Error:
        """Return Media instance or None."""

    @abc.abstractmethod
    async def delete_media(
            self,
            media_id: int,
    ) -> None | errors.Error:
        """Delete Media with given id, return True on success."""

    @abc.abstractmethod
    async def copy_media(
            self,
            owner_uuid: UUID,
            source_uuid: UUID,
            target_uuid: UUID,
            media_type: str,
            ext: str,
    ) -> int | errors.Error:
        """Save intention to copy data between items."""