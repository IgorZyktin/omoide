# -*- coding: utf-8 -*-
"""Use case for media.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces, exceptions
from omoide.presentation import api_models

__all__ = [
    'ReadMediaUseCase',
    'CreateOrUpdateMediaUseCase',
    'DeleteMediaUseCase',
]


class BaseMediaUseCase:
    """Base use case."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsRepository,
            media_repo: interfaces.AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.media_repo = media_repo

    async def _assert_has_access(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.AccessStatus:
        """Raise if user has no access to this Media."""
        access = await self.items_repo.check_access(user, uuid)

        if access.does_not_exist:
            raise exceptions.NotFound(f'Media {uuid} does not exist')

        if access.is_not_given:
            raise exceptions.Forbidden(f'User {user.uuid} ({user.name}) '
                                       f'has no access to item {uuid}')

        if access.is_not_owner:
            raise exceptions.Forbidden(f'You must own item {uuid} '
                                       'to be able to modify it')

        return access


class CreateOrUpdateMediaUseCase(BaseMediaUseCase):
    """Use case for updating an item."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
            payload: api_models.CreateMediaIn,
    ) -> bool:
        """Business logic."""
        # TODO(i.zyktin): implement item update
        print(f'CreateOrUpdateMediaUseCase: {payload.ext}, '
              f'{payload.type}, {len(payload.content)}')
        return False


class ReadMediaUseCase(BaseMediaUseCase):
    """Use case for getting an item."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.Media:
        await self._assert_has_access(user, uuid)
        media = await self.media_repo.read_media(uuid)

        if media is None:
            raise exceptions.NotFound(f'Media {uuid} does not exist')

        return media


class DeleteMediaUseCase(BaseMediaUseCase):
    """Use case for deleting an item."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> bool:
        """Business logic."""
        await self._assert_has_access(user, uuid)
        deleted = await self.media_repo.delete_media(uuid)

        if not deleted:
            raise exceptions.NotFound(f'Media {uuid} does not exist')

        return True
