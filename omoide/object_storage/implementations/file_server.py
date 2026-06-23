"""Object storage that saves data into files."""

from omoide import const
from omoide import models
from omoide.database.interfaces import AbsDatabase
from omoide.database.interfaces import AbsMediaRepo
from omoide.database.interfaces import AbsMiscRepo
from omoide.object_storage.interfaces.abs_object_storage import AbsObjectStorage


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
                        'media_type': const.THUMBNAIL,
                    },
                )
                copied_types.append(const.THUMBNAIL)

        return copied_types
