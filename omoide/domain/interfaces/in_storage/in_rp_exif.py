# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on EXIF records.
"""
import abc

from omoide.domain import models
from omoide.domain.errors import Error
from omoide.domain.interfaces.in_storage import in_rp_base
from omoide.domain.special_types import Result
from omoide.infra import impl


class AbsEXIFRepository(in_rp_base.AbsBaseRepository):
    """CRUD repository for EXIF."""

    @abc.abstractmethod
    async def create_exif(
            self,
            user: models.User,
            exif: models.EXIF,
    ) -> Result[Error, models.EXIF]:
        """Create."""

    @abc.abstractmethod
    async def read_exif(
            self,
            uuid: impl.UUID,
    ) -> Result[Error, models.EXIF]:
        """Read."""

    @abc.abstractmethod
    async def update_exif(
            self,
            user: models.User,
            exif: models.EXIF,
    ) -> Result[Error, models.EXIF]:
        """Update."""

    @abc.abstractmethod
    async def delete_exif(
            self,
            uuid: impl.UUID,
    ) -> Result[Error, impl.UUID]:
        """Delete."""
