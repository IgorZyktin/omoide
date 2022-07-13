# -*- coding: utf-8 -*-
"""Use case for EXIF.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces, exceptions
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
            items_repo: interfaces.AbsItemsRepository,
            exif_repo: interfaces.AbsEXIFRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.exif_repo = exif_repo

    async def _assert_has_access(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.AccessStatus:
        """Raise if user has no access to this EXIF."""
        access = await self.items_repo.check_access(user, uuid)

        if access.does_not_exist:
            raise exceptions.NotFound(f'Item {uuid} does not exist')

        if access.is_not_given:
            raise exceptions.Forbidden(f'User {user.uuid} ({user.name}) '
                                       f'has no access to item {uuid}')

        if access.is_not_owner:
            raise exceptions.Forbidden(f'You must own item {uuid} '
                                       'to be able to modify it')

        return access


class CreateOrUpdateEXIFUseCase(BaseEXIFUseCase):
    """Use case for updating an EXIF."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
            exif_in: api_models.EXIFIn,
    ) -> bool:
        """Business logic."""
        await self._assert_has_access(user, uuid)

        exif = domain.EXIF(
            item_uuid=uuid,
            exif=exif_in.exif,
        )

        return await self.exif_repo.create_or_update_exif(user, exif)


class ReadEXIFUseCase(BaseEXIFUseCase):
    """Use case for getting an EXIF."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.EXIF:
        await self._assert_has_access(user, uuid)
        exif = await self.exif_repo.read_exif(uuid)

        if exif is None:
            raise exceptions.NotFound(f'EXIF {uuid} does not exist')

        return exif


class DeleteEXIFUseCase(BaseEXIFUseCase):
    """Use case for deleting an EXIF."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> bool:
        """Business logic."""
        await self._assert_has_access(user, uuid)
        deleted = await self.exif_repo.delete_exif(uuid)

        if not deleted:
            raise exceptions.NotFound(f'EXIF {uuid} does not exist')

        return True
