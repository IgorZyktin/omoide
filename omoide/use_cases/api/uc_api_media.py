"""Use cases for media."""
from uuid import UUID

from omoide import const
from omoide import models
from omoide.domain import actions
from omoide.domain import exceptions
from omoide.domain.core import core_models
from omoide.domain.interfaces import AbsPolicy
from omoide.storage import interfaces as storage_interfaces

__all__ = [
    'CreateMediaUseCase',
    'ApiCopyImageUseCase',
]


class CreateMediaUseCase:
    """Use case for uploading media content."""

    def __init__(
            self,
            policy: AbsPolicy,
            media_repo: storage_interfaces.AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        self.policy = policy
        self.media_repo = media_repo

    async def execute(
            self,
            user: models.User,
            item_uuid: UUID,
            media: core_models.Media,
    ) -> core_models.Media:
        """Business logic."""
        async with self.media_repo.transaction():
            await self.policy.check(user, item_uuid, actions.Media.CREATE)
            result = await self.media_repo.create_media(media)

        return result


class ApiCopyImageUseCase:
    """Use case for changing parent thumbnail."""

    def __init__(
            self,
            policy: AbsPolicy,
            items_repo: storage_interfaces.AbsItemsRepo,
            metainfo_repo: storage_interfaces.AbsMetainfoRepo,
            media_repo: storage_interfaces.AbsMediaRepository,
    ) -> None:
        """Initialize instance."""
        self.policy = policy
        self.items_repo = items_repo
        self.metainfo_repo = metainfo_repo
        self.media_repo = media_repo

    async def execute(
            self,
            user: models.User,
            source_uuid: UUID,
            target_uuid: UUID,
    ) -> None:
        """Business logic."""
        if target_uuid == source_uuid:
            raise exceptions.CircularReference(uuid1=source_uuid,
                                               uuid2=target_uuid)

        async with self.items_repo.transaction():
            await self.policy.check(user, source_uuid, actions.Item.UPDATE)
            await self.policy.check(user, target_uuid, actions.Item.UPDATE)

            source = await self.items_repo.read_item(source_uuid)

            if source is None:
                raise exceptions.ItemDoesNotExistError(item_uuid=source_uuid)

            if source.content_ext is None:
                raise exceptions.ItemHasNoFieldError(item_uuid=source_uuid,
                                                     field='content_ext')

            if source.preview_ext is None:
                raise exceptions.ItemHasNoFieldError(item_uuid=source_uuid,
                                                     field='preview_ext')

            if source.thumbnail_ext is None:
                raise exceptions.ItemHasNoFieldError(item_uuid=source_uuid,
                                                     field='thumbnail_ext')

            for each in (const.CONTENT,
                         const.PREVIEW,
                         const.THUMBNAIL):
                await self.media_repo.copy_image(
                    owner_uuid=source.owner_uuid,
                    source_uuid=source_uuid,
                    target_uuid=target_uuid,
                    media_type=each,
                    ext=getattr(source, f'{each}_ext', ''),
                )

            await self.metainfo_repo.update_metainfo_extras(
                target_uuid, {'copied_image_from': str(source_uuid)})

            await self.metainfo_repo.mark_metainfo_updated(target_uuid)

        return None
