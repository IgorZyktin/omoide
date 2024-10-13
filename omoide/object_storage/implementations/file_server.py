"""Object storage that saves data into files."""

from omoide import const
from omoide import models
from omoide import utils
from omoide.object_storage.interfaces.abs_object_storage import (
    AbsObjectStorage,
)
from omoide.storage.interfaces.repositories.abs_media_repo import AbsMediaRepo


class FileObjectStorage(AbsObjectStorage):
    """Object storage that saves data into files.

    This implementation is server-side. It does not
    actually have access to the filesystem. It can
    only operate with media records on the database.
    """

    def __init__(self, media_repo: AbsMediaRepo, prefix_size: int) -> None:
        """Initialize instance."""
        self.media_repo = media_repo
        self.prefix_size = prefix_size

    async def save_object(
        self,
        item: models.Item,
        media_type: const.MEDIA_TYPE,
        binary_content: bytes,
        ext: str,
    ) -> None:
        """Save object of specific content type."""
        media = models.Media(
            id=-1,
            created_at=utils.now(),
            processed_at=None,
            error=None,
            owner_uuid=item.owner_uuid,
            item_uuid=item.uuid,
            media_type=media_type,
            content=binary_content,
            ext=ext,
        )
        await self.media_repo.create_media(media)

    async def delete_all_objects(
        self,
        item: models.Item,
    ) -> list[const.MEDIA_TYPE]:
        """Delete all objects for given item."""
        deleted_types: list[const.MEDIA_TYPE] = []
        now = utils.now()

        if item.content_ext:
            await self.media_repo.mark_file_as_orphan(
                item=item,
                media_type=const.CONTENT,
                ext=item.content_ext,
                moment=now,
            )
            deleted_types.append(const.CONTENT)

        if item.preview_ext:
            await self.media_repo.mark_file_as_orphan(
                item=item,
                media_type=const.PREVIEW,
                ext=item.preview_ext,
                moment=now,
            )
            deleted_types.append(const.PREVIEW)

        if item.thumbnail_ext:
            await self.media_repo.mark_file_as_orphan(
                item=item,
                media_type=const.THUMBNAIL,
                ext=item.thumbnail_ext,
                moment=now,
            )
            deleted_types.append(const.THUMBNAIL)

        return deleted_types

    async def copy_all_objects(
        self,
        source_item: models.Item,
        target_item: models.Item,
    ) -> list[const.MEDIA_TYPE]:
        """Copy all objects from one item to another."""
        copied_types: list[const.MEDIA_TYPE] = []
        now = utils.now()

        if source_item.content_ext is not None:
            await self.media_repo.copy_image(
                source_item=source_item,
                target_item=target_item,
                media_type=const.CONTENT,
                ext=source_item.content_ext,
                moment=now,
            )
            copied_types.append(const.CONTENT)

        if source_item.preview_ext is not None:
            await self.media_repo.copy_image(
                source_item=source_item,
                target_item=target_item,
                media_type=const.PREVIEW,
                ext=source_item.preview_ext,
                moment=now,
            )
            copied_types.append(const.PREVIEW)

        if source_item.thumbnail_ext is not None:
            await self.media_repo.copy_image(
                source_item=source_item,
                target_item=target_item,
                media_type=const.THUMBNAIL,
                ext=source_item.thumbnail_ext,
                moment=now,
            )
            copied_types.append(const.THUMBNAIL)

        return copied_types
