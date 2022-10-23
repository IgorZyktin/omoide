# -*- coding: utf-8 -*-
"""Use case for media.
"""
import base64
from uuid import UUID

from omoide import domain, utils
from omoide.domain import interfaces, errors, actions
from omoide.infra.special_types import Result, Failure, Success
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
            media_repo: interfaces.AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        self.media_repo = media_repo


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
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            media_type: str,
            media: api_models.CreateMediaIn,
    ) -> Result[errors.Error, bool]:
        """Business logic."""
        async with self.media_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Media.CREATE_OR_UPDATE)

            if error:
                return Failure(error)

            valid_media = domain.Media(
                item_uuid=uuid,
                created_at=utils.now(),
                processed_at=None,
                status='init',
                content=self.extract_binary_content(media.content),
                ext=media.ext,
                media_type=media_type,
            )

            created = await self.media_repo.create_or_update_media(user,
                                                                   valid_media)
        return Success(created)


class ReadMediaUseCase(BaseMediaUseCase):
    """Use case for getting an item."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            media_type: str,
    ) -> Result[errors.Error, domain.Media]:
        async with self.media_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Media.READ)

        if error:
            return Failure(error)

        media = await self.media_repo.read_media(uuid, media_type)

        if media is None:
            return Failure(errors.MediaDoesNotExist(uuid=uuid))

        return Success(media)


class DeleteMediaUseCase(BaseMediaUseCase):
    """Use case for deleting an item."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            media_type: str,
    ) -> Result[errors.Error, bool]:
        """Business logic."""
        async with self.media_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Media.DELETE)

            if error:
                return Failure(error)

            deleted = await self.media_repo.delete_media(uuid, media_type)

            if not deleted:
                return Failure(errors.MediaDoesNotExist(uuid=uuid))

        return Success(True)
