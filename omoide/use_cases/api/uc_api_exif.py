# -*- coding: utf-8 -*-
"""Use case for EXIF.
"""
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import models
from omoide.domain.interfaces.in_infra import in_policy
from omoide.domain.interfaces.in_storage import in_rp_exif
from omoide.domain.special_types import Failure
from omoide.domain.special_types import Result
from omoide.infra import impl

__all__ = [
    'CreateEXIFUseCase',
    'ReadEXIFUseCase',
    'UpdateEXIFUseCase',
    'DeleteEXIFUseCase',
]


class BaseEXIFUseCase:
    """Base use case."""

    def __init__(self, exif_repo: in_rp_exif.AbsEXIFRepository) -> None:
        """Initialize instance."""
        self.exif_repo = exif_repo


class CreateEXIFUseCase(BaseEXIFUseCase):
    """Use case for creation an EXIF."""

    async def execute(
            self,
            policy: in_policy.AbsPolicy,
            user: models.User,
            exif: models.EXIF,
    ) -> Result[errors.Error, models.EXIF]:
        """Business logic."""
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, exif.item_uuid,
                                               actions.EXIF.CREATE)
            if error:
                return Failure(error)

            result = await self.exif_repo.create_exif(user, exif)

        return result


class ReadEXIFUseCase(BaseEXIFUseCase):
    """Use case for getting an EXIF."""

    async def execute(
            self,
            policy: in_policy.AbsPolicy,
            user: models.User,
            item_uuid: impl.UUID,
    ) -> Result[errors.Error, models.EXIF]:
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, item_uuid,
                                               actions.EXIF.READ)
            if error:
                return Failure(error)

            result = await self.exif_repo.read_exif(item_uuid)

        return result


class UpdateEXIFUseCase(BaseEXIFUseCase):
    """Use case for updating an EXIF."""

    async def execute(
            self,
            policy: in_policy.AbsPolicy,
            user: models.User,
            exif: models.EXIF,
    ) -> Result[errors.Error, models.EXIF]:
        """Business logic."""
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, exif.item_uuid,
                                               actions.EXIF.UPDATE)
            if error:
                return Failure(error)

            result = await self.exif_repo.update_exif(user, exif)

        return result


class DeleteEXIFUseCase(BaseEXIFUseCase):
    """Use case for deleting EXIF."""

    async def execute(
            self,
            policy: in_policy.AbsPolicy,
            user: models.User,
            item_uuid: impl.UUID,
    ) -> Result[errors.Error, bool]:
        """Business logic."""
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, item_uuid,
                                               actions.EXIF.DELETE)
            if error:
                return Failure(error)

            result = await self.exif_repo.delete_exif(item_uuid)

        return result
