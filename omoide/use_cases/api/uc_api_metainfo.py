"""Use case for Metainfo.
"""
from uuid import UUID

from omoide import utils
from omoide.domain import actions
from omoide.domain import interfaces
from omoide.domain.core import core_models
from omoide.domain.interfaces import AbsPolicy

__all__ = [
    'UpdateMetainfoUseCase',
    'ReadMetainfoUseCase',
]


class BaseMetainfoUseCase:
    """Base use case."""

    def __init__(
            self,
            policy: AbsPolicy,
            meta_repo: interfaces.AbsMetainfoRepository,
    ) -> None:
        """Initialize instance."""
        self.policy = policy
        self.meta_repo = meta_repo


class UpdateMetainfoUseCase(BaseMetainfoUseCase):
    """Use case for updating Metainfo."""

    async def execute(
            self,
            user: core_models.User,
            item_uuid: UUID,
            metainfo: core_models.Metainfo,
    ) -> None:
        """Business logic."""
        async with self.meta_repo.transaction():
            await self.policy.check(user, item_uuid, actions.Metainfo.UPDATE)

            current_metainfo = await self.meta_repo.read_metainfo(item_uuid)

            current_metainfo.updated_at = utils.now()

            current_metainfo.user_time = metainfo.user_time
            current_metainfo.content_type = metainfo.content_type

            current_metainfo.author = metainfo.author
            current_metainfo.author_url = metainfo.author_url
            current_metainfo.saved_from_url = metainfo.saved_from_url
            current_metainfo.description = metainfo.description
            current_metainfo.extras = metainfo.extras

            current_metainfo.content_size = metainfo.content_size
            current_metainfo.preview_size = metainfo.preview_size
            current_metainfo.thumbnail_size = metainfo.thumbnail_size

            current_metainfo.content_width = metainfo.content_width
            current_metainfo.content_height = metainfo.content_height
            current_metainfo.preview_width = metainfo.preview_width
            current_metainfo.preview_height = metainfo.preview_height
            current_metainfo.thumbnail_width = metainfo.thumbnail_width
            current_metainfo.thumbnail_height = metainfo.thumbnail_height

            await self.meta_repo.update_metainfo(user, current_metainfo)

        return None


class ReadMetainfoUseCase(BaseMetainfoUseCase):
    """Use case for getting Metainfo."""

    async def execute(
            self,
            user: core_models.User,
            item_uuid: UUID,
    ) -> core_models.Metainfo:
        async with self.meta_repo.transaction():
            await self.policy.check(user, item_uuid, actions.Metainfo.READ)
            metainfo = await self.meta_repo.read_metainfo(item_uuid)

        return metainfo
