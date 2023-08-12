"""Use cases for media.
"""
from uuid import UUID

from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.domain.core import core_models
from omoide.domain.storage.interfaces.in_rp_media import AbsMediaRepository

__all__ = [
    'CreateMediaUseCase',
]


class CreateMediaUseCase:
    """Use case for uploading media content."""

    def __init__(
            self,
            media_repo: AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        self.media_repo = media_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: core_models.User,
            uuid: UUID,
            media: core_models.Media,
    ) -> core_models.Media | errors.Error:
        """Business logic."""
        async with self.media_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Media.CREATE)
            if error:
                return error

            created_media = await self.media_repo.create_media(media)

        return created_media
