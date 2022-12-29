# -*- coding: utf-8 -*-
"""Use case for Metainfo.
"""
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
    'UpdateMetainfoUseCase',
    'ReadMetainfoUseCase',
]


class BaseMetainfoUseCase:
    """Base use case."""

    def __init__(
            self,
            meta_repo: interfaces.AbsMetainfoRepository,
    ) -> None:
        """Initialize instance."""
        self.meta_repo = meta_repo


class UpdateMetainfoUseCase(BaseMetainfoUseCase):
    """Use case for updating Metainfo."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            metainfo_in: api_models.MetainfoIn,
    ) -> Result[errors.Error, bool]:
        """Business logic."""
        async with self.meta_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Metainfo.UPDATE)

            if error:
                return Failure(error)

            metainfo = await self.meta_repo.read_metainfo(uuid)

            if metainfo is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            metainfo.updated_at = utils.now()

            metainfo.user_time = metainfo_in.user_time
            metainfo.media_type = metainfo_in.media_type

            metainfo.author = metainfo_in.author
            metainfo.author_url = metainfo_in.author_url
            metainfo.saved_from_url = metainfo_in.saved_from_url
            metainfo.description = metainfo_in.description
            metainfo.extras = metainfo_in.extras

            metainfo.content_size = metainfo_in.content_size
            metainfo.preview_size = metainfo_in.preview_size
            metainfo.thumbnail_size = metainfo_in.thumbnail_size

            metainfo.content_width = metainfo_in.content_width
            metainfo.content_height = metainfo_in.content_height
            metainfo.preview_width = metainfo_in.preview_width
            metainfo.preview_height = metainfo_in.preview_height
            metainfo.thumbnail_width = metainfo_in.thumbnail_width
            metainfo.thumbnail_height = metainfo_in.thumbnail_height

            await self.meta_repo.update_metainfo(user, metainfo)

        return Success(True)


class ReadMetainfoUseCase(BaseMetainfoUseCase):
    """Use case for getting Metainfo."""

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, domain.Metainfo]:
        async with self.meta_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Metainfo.READ)
            if error:
                return Failure(error)

            metainfo = await self.meta_repo.read_metainfo(uuid)

            if metainfo is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

        return Success(metainfo)
