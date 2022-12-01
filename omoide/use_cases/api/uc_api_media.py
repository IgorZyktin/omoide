# -*- coding: utf-8 -*-
"""Use case for media.
"""
import base64
from uuid import UUID

from omoide import domain
from omoide import utils
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.presentation import api_models

__all__ = [
    'ReadMediaUseCase',
    'CreateMediaUseCase',
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


class CreateMediaUseCase(BaseMediaUseCase):
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
            media: api_models.CreateMediaIn,
    ) -> Result[errors.Error, int]:
        """Business logic."""
        async with self.media_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Media.CREATE)
            if error:
                return Failure(error)

            valid_media = domain.Media(
                id=-1,
                owner_uuid=user.uuid,
                item_uuid=uuid,
                created_at=utils.now(),
                processed_at=None,
                content=self.extract_binary_content(media.content),
                ext=media.ext,
                media_type=media.media_type,
                replication={},
                error='',
            )

            media_id = await self.media_repo.create_media(user, valid_media)

        return Success(media_id)


class ReadMediaUseCase(BaseMediaUseCase):
    """Use case for getting an item."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            media_id: int,
    ) -> Result[errors.Error, domain.Media]:
        async with self.media_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Media.READ)
            if error:
                return Failure(error)

            media = await self.media_repo.read_media(media_id)
            if media is None:
                return Failure(
                    errors.MediaDoesNotExist(uuid=uuid, id=media_id)
                )

        return Success(media)


class DeleteMediaUseCase(BaseMediaUseCase):
    """Use case for deleting an item."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            media_id: int,
    ) -> Result[errors.Error, bool]:
        """Business logic."""
        async with self.media_repo.transaction():
            media = await self.media_repo.read_media(media_id)

            if media is None:
                return Failure(
                    errors.MediaDoesNotExist(uuid=uuid, id=media_id)
                )

            error = await policy.is_restricted(user, media.item_uuid,
                                               actions.Media.DELETE)
            if error:
                return Failure(error)

            deleted = await self.media_repo.delete_media(media_id)

            if not deleted:
                return Failure(
                    errors.MediaDoesNotExist(uuid=uuid, id=media_id)
                )

        return Success(True)
