"""Repository that perform CRUD operations on EXIF records.
"""
import abc
from uuid import UUID

from omoide.domain.core import core_models
from omoide.domain.storage.interfaces.in_rp_base import AbsBaseRepository


class AbsEXIFRepository(AbsBaseRepository):
    """Repository that perform CRUD operations on EXIF records."""

    @abc.abstractmethod
    async def create_exif(self, exif: core_models.EXIF) -> core_models.EXIF:
        """Create EXIF."""

    @abc.abstractmethod
    async def update_exif(self, exif: core_models.EXIF) -> core_models.EXIF:
        """Update EXIF."""

    @abc.abstractmethod
    async def get_exif_by_item_uuid(self, item_uuid: UUID) -> core_models.EXIF:
        """Return EXIF."""

    @abc.abstractmethod
    async def delete_exif(self, item_uuid: UUID) -> None:
        """Delete EXIF."""
