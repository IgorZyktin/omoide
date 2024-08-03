"""Object storage that saves data into files."""
from omoide import const
from omoide import models
from omoide import utils
from omoide.storage.interfaces.repositories.abs_media_repo import AbsMediaRepo
from omoide.storage.object_storage.interfaces.abs_object_storage import (
    AbsObjectStorage
)


class FileObjectStorageServer(AbsObjectStorage):
    """Object storage that saves data into files.

    This implementation is server-side. It does not
    actually have access to the filesystem. It can
    only operate with media records on the database.
    """

    def __init__(
        self,
        media_repo: AbsMediaRepo,
        prefix_size: int,
    ) -> None:
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

    async def delete_all_objects(self, item: models.Item) -> None:
        """Delete all objects for given item."""
        # TODO - we're actually doing nothing here. Probably should
        #  rename original files, but not really delete them

    async def copy_all_objects(
        self,
        source_item: models.Item,
        target_item: models.Item,
    ) -> list[const.MEDIA_TYPE]:
        """Copy all objects from one item to another."""
        media_types: list[const.MEDIA_TYPE] = []

        if source_item.content_ext is not None:
            await self.media_repo.copy_image(
                owner_uuid=source_item.owner_uuid,
                source_uuid=source_item.uuid,
                target_uuid=target_item.uuid,
                media_type=const.CONTENT,
                ext=source_item.content_ext,
            )
            media_types.append(const.CONTENT)

        if source_item.preview_ext is not None:
            await self.media_repo.copy_image(
                owner_uuid=source_item.owner_uuid,
                source_uuid=source_item.uuid,
                target_uuid=target_item.uuid,
                media_type=const.PREVIEW,
                ext=source_item.preview_ext,
            )
            media_types.append(const.PREVIEW)

        if source_item.thumbnail_ext is not None:
            await self.media_repo.copy_image(
                owner_uuid=source_item.owner_uuid,
                source_uuid=source_item.uuid,
                target_uuid=target_item.uuid,
                media_type=const.THUMBNAIL,
                ext=source_item.thumbnail_ext,
            )
            media_types.append(const.THUMBNAIL)

        return media_types
