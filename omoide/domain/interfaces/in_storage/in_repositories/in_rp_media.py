"""Repository that perform CRUD operations on media records.
"""
import abc
from uuid import UUID

from omoide.domain.core import core_models
from omoide.domain.interfaces.in_storage.in_repositories.in_rp_base import (
    AbsBaseRepository,
)


class AbsMediaRepository(AbsBaseRepository):
    """Repository that perform CRUD operations on media records."""

    @abc.abstractmethod
    async def create_media(
        self,
        media: core_models.Media,
    ) -> core_models.Media:
        """Create Media, return media id."""

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
