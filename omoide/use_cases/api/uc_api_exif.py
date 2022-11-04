# -*- coding: utf-8 -*-
"""Use case for EXIF.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.presentation import api_models

__all__ = [
    'CreateOrUpdateEXIFUseCase',
    'ReadEXIFUseCase',
    'DeleteEXIFUseCase',
]


class BaseEXIFUseCase:
    """Base use case."""

    def __init__(
            self,
            exif_repo: interfaces.AbsEXIFRepository,
    ) -> None:
        """Initialize instance."""
        self.exif_repo = exif_repo


class CreateOrUpdateEXIFUseCase(BaseEXIFUseCase):
    """Use case for updating an EXIF."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            exif_in: api_models.EXIFIn,
    ) -> Result[errors.Error, bool]:
        """Business logic."""
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.EXIF.CREATE_OR_UPDATE)

            if error:
                return Failure(error)

            exif = domain.EXIF(
                item_uuid=uuid,
                exif=exif_in.exif,
            )

            created = await self.exif_repo.create_or_update_exif(user, exif)

        return Success(created)


class ReadEXIFUseCase(BaseEXIFUseCase):
    """Use case for getting an EXIF."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, domain.EXIF]:
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.EXIF.READ)

            if error:
                return Failure(error)

            exif = await self.exif_repo.read_exif(uuid)

            if exif is None:
                return Failure(errors.EXIFDoesNotExist(uuid=uuid))

        return Success(exif)


class DeleteEXIFUseCase(BaseEXIFUseCase):
    """Use case for deleting an EXIF."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, bool]:
        """Business logic."""
        async with self.exif_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.EXIF.DELETE)

            if error:
                return Failure(error)

            deleted = await self.exif_repo.delete_exif(uuid)

            if not deleted:
                return Failure(errors.EXIFDoesNotExist(uuid=uuid))

        return Success(True)
