# -*- coding: utf-8 -*-
"""Use case for media.
"""
import base64
from uuid import UUID

from omoide import domain, utils
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
            raise exceptions.NotFound(f'Item {uuid} does not exist')

        if access.is_not_given:
            raise exceptions.Forbidden(f'User {user.uuid} ({user.name}) '
                                       f'has no access to item {uuid}')

        if access.is_not_owner:
            raise exceptions.Forbidden(f'You must own item {uuid} '
                                       'to be able to modify it')

        return access


class CreateOrUpdateMediaUseCase(BaseMediaUseCase):
    """Use case for updating an item."""

    @staticmethod
    def extract_binary_content(raw_content: str) -> bytes:
        """Convert from base64 into bytes."""
        sep = raw_content.index(',')
        body = raw_content[sep + 1:]
        return base64.decodebytes(body.encode('utf-8'))

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
            media_type: str,
            media: api_models.CreateMediaIn,
    ) -> bool:
        """Business logic."""
        await self._assert_has_access(user, uuid)

        valid_media = domain.Media(
            item_uuid=uuid,
            created_at=utils.now(),
            processed_at=None,
            status='init',
            content=self.extract_binary_content(media.content),
            ext=media.ext,
            media_type=media_type,
        )

        return await self.media_repo.create_or_update_media(user, valid_media)


class ReadMediaUseCase(BaseMediaUseCase):
    """Use case for getting an item."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
            media_type: str,
    ) -> domain.Media:
        await self._assert_has_access(user, uuid)
        media = await self.media_repo.read_media(uuid, media_type)

        if media is None:
            raise exceptions.NotFound(f'Media {uuid} does not exist')

        return media


class DeleteMediaUseCase(BaseMediaUseCase):
    """Use case for deleting an item."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
            media_type: str,
    ) -> bool:
        """Business logic."""
        await self._assert_has_access(user, uuid)
        deleted = await self.media_repo.delete_media(uuid, media_type)

        if not deleted:
            raise exceptions.NotFound(f'Media {uuid} does not exist')

        return True
