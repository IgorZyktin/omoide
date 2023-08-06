# -*- coding: utf-8 -*-
"""Use cases for media.
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
    'CreateMediaUseCase',
]


class CreateMediaUseCase:
    """Use case for uploading media content."""

    def __init__(
            self,
            media_repo: interfaces.AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        self.media_repo = media_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
            media_in: list[api_models.CreateMediaIn],
    ) -> Result[errors.Error, int]:
        """Business logic."""
        async with self.media_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Media.CREATE)
            if error:
                return Failure(error)


                media_id = await self.media_repo.create_media(user, media)

        return Success(media_id)
