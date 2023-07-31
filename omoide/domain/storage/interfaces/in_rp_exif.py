"""Repository that perform CRUD operations on EXIF records.
"""
import abc
from uuid import UUID

from omoide.domain.core import core_models
from omoide.domain.errors import Error
from omoide.domain.storage.interfaces.in_rp_base import AbsBaseRepository


class AbsEXIFRepository(AbsBaseRepository):
    """Repository that perform CRUD operations on EXIF records."""

    @abc.abstractmethod
    async def create_exif(
            self,
            exif: core_models.EXIF,
    ) -> core_models.EXIF | Error:
        """Create EXIF, return instance or error."""

    @abc.abstractmethod
    async def update_exif(
            self,
            exif: core_models.EXIF,
    ) -> core_models.EXIF | Error:
        """Update EXIF, return instance or error."""

    @abc.abstractmethod
    async def get_exif_by_item_uuid(
            self,
            item_uuid: UUID,
    ) -> core_models.EXIF | Error:
        """Return EXIF."""

    @abc.abstractmethod
    async def delete_exif(
            self,
            item_uuid: UUID,
    ) -> None | Error:
        """Delete EXIF."""
