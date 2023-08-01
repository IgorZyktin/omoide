"""Use cases for EXIF.
"""
from uuid import UUID

from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.domain.core import core_models
from omoide.domain.storage.interfaces.in_rp_exif import AbsEXIFRepository

__all__ = [
    'CreateEXIFUseCase',
    'ReadEXIFUseCase',
    'UpdateEXIFUseCase',
    'DeleteEXIFUseCase',
]


class BaseEXIFUseCase:
    """Base use case."""

    def __init__(
            self,
            exif_repo: AbsEXIFRepository,
    ) -> None:
        """Initialize instance."""
        self.exif_repo = exif_repo


class CreateEXIFUseCase(BaseEXIFUseCase):
    """Use case for creation an EXIF."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: core_models.User,
            item_uuid: UUID,
            exif: core_models.EXIF,
    ) -> core_models.EXIF | errors.Error:
        """Business logic."""
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, item_uuid,
                                               actions.EXIF.CREATE)
            if error:
                return error

            result = await self.exif_repo.create_exif(exif)

        return result


class ReadEXIFUseCase(BaseEXIFUseCase):
    """Use case for getting an EXIF."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: core_models.User,
            item_uuid: UUID,
    ) -> core_models.EXIF | errors.Error:
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, item_uuid,
                                               actions.EXIF.READ)
            if error:
                return error

            result = await self.exif_repo.get_exif_by_item_uuid(item_uuid)

        return result


class UpdateEXIFUseCase(BaseEXIFUseCase):
    """Use case for updating an EXIF."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: core_models.User,
            item_uuid: UUID,
            exif: core_models.EXIF,
    ) -> core_models.EXIF | errors.Error:
        """Business logic."""
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, item_uuid,
                                               actions.EXIF.UPDATE)
            if error:
                return error

            result = await self.exif_repo.update_exif(exif)

        return result


class DeleteEXIFUseCase(BaseEXIFUseCase):
    """Use case for deleting an EXIF."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: core_models.User,
            item_uuid: UUID,
    ) -> None | errors.Error:
        """Business logic."""
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, item_uuid,
                                               actions.EXIF.DELETE)
            if error:
                return error

            result = await self.exif_repo.delete_exif(item_uuid)

        return result
