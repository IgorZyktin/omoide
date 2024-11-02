"""Implementation for filesystem commands."""

from pathlib import Path
from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import utils
from omoide.database.implementations.impl_sqlalchemy import ItemsRepo
from omoide.database.implementations.impl_sqlalchemy import MetaRepo
from omoide.database.implementations.impl_sqlalchemy import SqlalchemyDatabase
from omoide.database.implementations.impl_sqlalchemy import UsersRepo
from omoide.object_storage.implementations.file_client import FileObjectStorageClient

LOG = custom_logging.get_logger(__name__)


async def refresh_file_sizes(
    db_url: str,
    folder: Path,
    verbose: bool,
    only_users: list[UUID] | None,
    only_items: list[UUID] | None,
    marker: int | None,
    batch_size: int,
    limit: int | None,
) -> int:
    """Get actual file size for every image and save them into DB."""
    users = UsersRepo()
    meta = MetaRepo()
    items = ItemsRepo()

    database = SqlalchemyDatabase(db_url)
    object_storage = FileObjectStorageClient(
        folder=folder,
        prefix_size=const.STORAGE_PREFIX_SIZE,
    )

    def condition(_total_in_batch: int, _batch_size: int) -> bool:
        """Cycle stop condition."""
        if limit is not None and total == limit:
            return False

        return not (_total_in_batch != 0 and _total_in_batch < _batch_size)

    async with database.transaction() as conn:
        only_user_ids = await users.cast_uuids(conn, only_users or [])
        only_item_ids = await items.cast_uuids(conn, only_items or [])

    total = 0
    total_in_batch = 0
    batch_number = 1
    last_seen = marker if marker is not None else None

    while condition(total_in_batch, batch_size):
        LOG.info('Batch {}', batch_number)
        async with database.transaction() as conn:
            local_items = await items.get_batch(
                conn=conn,
                only_users=only_user_ids,
                only_items=only_item_ids,
                batch_size=batch_size,
                last_seen=last_seen,
                limit=limit,
            )

            for item in local_items:
                last_seen = item.id
                total += 1
                total_in_batch += 1

                try:
                    sizes = object_storage.get_file_sizes(item)
                except Exception:
                    LOG.exception('Failed to process {}', item)
                    continue

                metainfo = await meta.get_by_item(conn, item)
                metainfo.content_size = sizes.content_size
                metainfo.preview_size = sizes.preview_size
                metainfo.thumbnail_size = sizes.thumbnail_size
                metainfo.updated_at = utils.now()
                await meta.save(conn, metainfo)

                if verbose:
                    total_bytes = (
                        (sizes.content_size or 0)
                        + (sizes.preview_size or 0)
                        + (sizes.thumbnail_size or 0)
                    )
                    total_hr = utils.human_readable_size(total_bytes)
                    LOG.info('Updated {}, total {}', item, total_hr)

            batch_number += 1

    return total


async def refresh_image_dimensions(
    db_url: str,
    folder: Path,
    verbose: bool,
    only_users: list[UUID] | None,
    only_items: list[UUID] | None,
    marker: int | None,
    batch_size: int,
    limit: int | None,
) -> int:
    """Get actual image size for every image and save them into DB."""
    users = UsersRepo()
    meta = MetaRepo()
    items = ItemsRepo()

    database = SqlalchemyDatabase(db_url)
    object_storage = FileObjectStorageClient(
        folder=folder,
        prefix_size=const.STORAGE_PREFIX_SIZE,
    )

    def condition(_total_in_batch: int, _batch_size: int) -> bool:
        """Cycle stop condition."""
        if limit is not None and total == limit:
            return False

        return not (_total_in_batch != 0 and _total_in_batch < _batch_size)

    async with database.transaction() as conn:
        only_user_ids = await users.cast_uuids(conn, only_users or [])
        only_item_ids = await items.cast_uuids(conn, only_items or [])

    total = 0
    total_in_batch = 0
    batch_number = 1
    last_seen = marker if marker is not None else None

    while condition(total_in_batch, batch_size):
        LOG.info('Batch {}', batch_number)
        async with database.transaction() as conn:
            local_items = await items.get_batch(
                conn=conn,
                only_users=only_user_ids,
                only_items=only_item_ids,
                batch_size=batch_size,
                last_seen=last_seen,
                limit=limit,
            )

            for item in local_items:
                last_seen = item.id
                total += 1
                total_in_batch += 1

                try:
                    dimensions = object_storage.get_dimensions_for_all_images(item)
                except Exception:
                    LOG.exception('Failed to process {}', item)
                    continue

                metainfo = await meta.get_by_item(conn, item)
                metainfo.content_width = dimensions.content.width
                metainfo.content_height = dimensions.content.height
                metainfo.preview_width = dimensions.preview.width
                metainfo.preview_height = dimensions.preview.height
                metainfo.thumbnail_width = dimensions.thumbnail.width
                metainfo.thumbnail_height = dimensions.thumbnail.height
                metainfo.updated_at = utils.now()
                await meta.save(conn, metainfo)

                if verbose:
                    LOG.info('Updated {}', item)

            batch_number += 1

    return total
