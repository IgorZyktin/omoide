"""Repository that perform CRUD operations on EXIF records.
"""
import abc

from omoide.domain import errors
from omoide.domain.core import core_models
from omoide.domain.storage.interfaces.in_rp_base import AbsBaseRepository
from omoide.infra import impl
from omoide.infra.special_types import *


class AbsEXIFRepository(AbsBaseRepository):
    """Repository that perform CRUD operations on EXIF records."""

    @abc.abstractmethod
    async def create_exif(
            self,
            exif: core_models.EXIF,
    ) -> Result[errors.Error, core_models.EXIF]:
        """Create EXIF, return instance or error."""

    @abc.abstractmethod
    async def update_exif(
            self,
            exif: core_models.EXIF,
    ) -> Result[errors.Error, core_models.EXIF]:
        """Update EXIF, return instance or error."""

    @abc.abstractmethod
    async def get_exif_by_item_uuid(
            self,
            item_uuid: impl.UUID,
    ) -> Result[errors.Error, core_models.EXIF]:
        """Return EXIF."""

    @abc.abstractmethod
    async def delete_exif(
            self,
            item_uuid: impl.UUID,
    ) -> Result[errors.Error, None]:
        """Delete EXIF."""
