"""Object storage that saves data into files."""

import python_utilz as pu

from omoide import const
from omoide import models
from omoide.database.interfaces import AbsDatabase
from omoide.database.interfaces import AbsMediaRepo
from omoide.database.interfaces import AbsMiscRepo
from omoide.object_storage.interfaces.abs_object_storage import AbsObjectStorage
from omoide.object_storage.interfaces.abs_object_storage import SoftDeleteEntry


class FileObjectStorageServer(AbsObjectStorage):
    """Object storage that saves data into files.

    This implementation is server-side. It does not
    actually have access to the filesystem. It can
    only operate with media records on the database.
    """

    def __init__(
        self,
        database: AbsDatabase,
        media: AbsMediaRepo,
        misc: AbsMiscRepo,
        prefix_size: int,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.media = media
        self.misc = misc
        self.prefix_size = prefix_size

    async def save(
        self,
        item: models.Item,
        media_type: const.MEDIA_TYPE,
        binary_content: bytes,
        ext: str,
    ) -> None:
        """Save object of specific content type."""
        media = models.Media(
            id=-1,
            created_at=pu.now(),
            processed_at=None,
            error=None,
            owner_id=item.owner_id,
            item_id=item.id,
            media_type=media_type,
            content=binary_content,
            ext=ext,
        )

        async with self.database.transaction() as conn:
            await self.media.create_media(conn, media)

    async def soft_delete(
        self,
        requested_by: models.User,
        item: models.Item,
    ) -> list[SoftDeleteEntry]:
        """Mark all objects as deleted."""
        deleted_types: list[SoftDeleteEntry] = []

        async with self.database.transaction() as conn:
            if item.content_ext:
                operation_id = await self.misc.create_parallel_operation(
                    conn=conn,
                    request=models.SoftDeleteMediaRequest(
                        requested_by_user_id=requested_by.id,
                        owner_uuid=item.owner_uuid,
                        item_uuid=item.uuid,
                        media_type=const.CONTENT,
                    ),
                )
                deleted_types.append({'media_type': const.CONTENT, 'operation_id': operation_id})

            if item.preview_ext:
                operation_id = await self.misc.create_parallel_operation(
                    conn=conn,
                    request=models.SoftDeleteMediaRequest(
                        requested_by_user_id=requested_by.id,
                        owner_uuid=item.owner_uuid,
                        item_uuid=item.uuid,
                        media_type=const.PREVIEW,
                    ),
                )
                deleted_types.append({'media_type': const.PREVIEW, 'operation_id': operation_id})

            if item.thumbnail_ext:
                operation_id = await self.misc.create_parallel_operation(
                    conn=conn,
                    request=models.SoftDeleteMediaRequest(
                        requested_by_user_id=requested_by.id,
                        owner_uuid=item.owner_uuid,
                        item_uuid=item.uuid,
                        media_type=const.THUMBNAIL,
                    ),
                )
                deleted_types.append({'media_type': const.THUMBNAIL, 'operation_id': operation_id})

        return deleted_types

    async def copy_all_objects(
        self,
        source_item: models.Item,
        target_item: models.Item,
    ) -> list[const.MEDIA_TYPE]:
        """Copy all objects from one item to another."""
        copied_types: list[const.MEDIA_TYPE] = []
        now = pu.now()

        async with self.database.transaction() as conn:
            if source_item.content_ext is not None:
                await self.media.copy_image(
                    conn=conn,
                    source_item=source_item,
                    target_item=target_item,
                    media_type=const.CONTENT,
                    ext=source_item.content_ext,
                    moment=now,
                )
                copied_types.append(const.CONTENT)

            if source_item.preview_ext is not None:
                await self.media.copy_image(
                    conn=conn,
                    source_item=source_item,
                    target_item=target_item,
                    media_type=const.PREVIEW,
                    ext=source_item.preview_ext,
                    moment=now,
                )
                copied_types.append(const.PREVIEW)

            if source_item.thumbnail_ext is not None:
                await self.media.copy_image(
                    conn=conn,
                    source_item=source_item,
                    target_item=target_item,
                    media_type=const.THUMBNAIL,
                    ext=source_item.thumbnail_ext,
                    moment=now,
                )
                copied_types.append(const.THUMBNAIL)

        return copied_types
