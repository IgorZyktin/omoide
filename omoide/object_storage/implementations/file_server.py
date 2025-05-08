"""Object storage that saves data into files."""

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

    async def soft_delete(
        self,
        requested_by: models.User,
        owner: models.User,
        item: models.Item,
    ) -> list[SoftDeleteEntry]:
        """Mark all objects as deleted."""
        deleted_types: list[SoftDeleteEntry] = []

        async with self.database.transaction() as conn:
            if item.content_ext:
                operation_id = await self.misc.create_parallel_operation(
                    conn=conn,
                    name='soft_delete',
                    extras={
                        'requested_by': str(requested_by.uuid),
                        'owner_uuid': str(owner.uuid),
                        'item_uuid': str(item.uuid),
                        'media_type': const.CONTENT,
                    },
                )
                deleted_types.append({'media_type': const.CONTENT, 'operation_id': operation_id})

            if item.preview_ext:
                operation_id = await self.misc.create_parallel_operation(
                    conn=conn,
                    name='soft_delete',
                    extras={
                        'requested_by': str(requested_by.uuid),
                        'owner_uuid': str(owner.uuid),
                        'item_uuid': str(item.uuid),
                        'media_type': const.PREVIEW,
                    },
                )
                deleted_types.append({'media_type': const.PREVIEW, 'operation_id': operation_id})

            if item.thumbnail_ext:
                operation_id = await self.misc.create_parallel_operation(
                    conn=conn,
                    name='soft_delete',
                    extras={
                        'requested_by': str(requested_by.uuid),
                        'owner_uuid': str(owner.uuid),
                        'item_uuid': str(item.uuid),
                        'media_type': const.THUMBNAIL,
                    },
                )
                deleted_types.append({'media_type': const.THUMBNAIL, 'operation_id': operation_id})

        return deleted_types

    async def copy_all_objects(
        self,
        requested_by: models.User,
        owner: models.User,
        source_item: models.Item,
        target_item: models.Item,
    ) -> list[const.MEDIA_TYPE]:
        """Copy all objects from one item to another."""
        copied_types: list[const.MEDIA_TYPE] = []

        async with self.database.transaction() as conn:
            if source_item.content_ext is not None:
                await self.misc.create_parallel_operation(
                    conn=conn,
                    name='copy',
                    extras={
                        'requested_by': str(requested_by.uuid),
                        'owner_uuid': str(owner.uuid),
                        'source_item_uuid': str(source_item.uuid),
                        'target_item_uuid': str(target_item.uuid),
                        'media_type': const.CONTENT,
                    },
                )
                copied_types.append(const.CONTENT)

            if source_item.preview_ext is not None:
                await self.misc.create_parallel_operation(
                    conn=conn,
                    name='copy',
                    extras={
                        'requested_by': str(requested_by.uuid),
                        'owner_uuid': str(owner.uuid),
                        'source_item_uuid': str(source_item.uuid),
                        'target_item_uuid': str(target_item.uuid),
                        'media_type': const.PREVIEW,
                    },
                )
                copied_types.append(const.PREVIEW)

            if source_item.thumbnail_ext is not None:
                await self.misc.create_parallel_operation(
                    conn=conn,
                    name='copy',
                    extras={
                        'requested_by': str(requested_by.uuid),
                        'owner_uuid': str(owner.uuid),
                        'source_item_uuid': str(source_item.uuid),
                        'target_item_uuid': str(target_item.uuid),
                        'media_type': const.PREVIEW,
                    },
                )
                copied_types.append(const.THUMBNAIL)

        return copied_types
