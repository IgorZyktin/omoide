"""Implementation for database commands."""

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import const
from omoide import custom_logging
from omoide import exceptions
from omoide.database import db_models
from omoide.database.implementations.impl_sqlalchemy import ItemsRepo
from omoide.database.implementations.impl_sqlalchemy import MediaRepo
from omoide.database.implementations.impl_sqlalchemy import MetaRepo
from omoide.database.implementations.impl_sqlalchemy import SqlalchemyDatabase
from omoide.object_storage.implementations.file_server import FileObjectStorageServer

LOG = custom_logging.get_logger(__name__)


async def copy_images_from_children(
    db_url: str,
    verbose: bool,
    only_users: list[UUID] | None,
    only_items: list[UUID] | None,
    limit: int | None,
) -> int:
    """Force items to copy images from their children."""
    total = 0

    items = ItemsRepo()
    meta = MetaRepo()
    media = MediaRepo()

    database = SqlalchemyDatabase(db_url)
    object_storage = FileObjectStorageServer(
        database=database,
        media=media,
        prefix_size=const.STORAGE_PREFIX_SIZE,
    )

    async with database.transaction() as conn:
        rows = await get_items_without_images(conn, only_users, only_items, limit)
        for item_uuid, name, copied_image_from_uuid in rows:
            changed = False
            target_item = await items.get_by_uuid(conn, item_uuid)

            if copied_image_from_uuid is not None:
                try:
                    source_item = await items.get_by_uuid(conn, UUID(copied_image_from_uuid))
                except exceptions.DoesNotExistError:
                    pass
                else:
                    if verbose:
                        LOG.info(
                            'Will get images for {target_item} using old source {source_item}',
                            target_item=target_item,
                            source_item=source_item,
                        )

                    await object_storage.copy_all_objects(
                        source_item=source_item,
                        target_item=target_item,
                    )
                    total += 1
                    continue

            children = await items.get_children(conn, target_item)

            child = None
            for child in children:
                if all(
                    (
                        child.content_ext is not None,
                        child.preview_ext is not None,
                        child.thumbnail_ext is not None,
                    )
                ):
                    break

            if child is not None:
                if verbose:
                    LOG.info(
                        'Will get images for {target_item} from child {source_item}',
                        target_item=target_item,
                        source_item=child,
                    )
                await object_storage.copy_all_objects(
                    source_item=child,
                    target_item=target_item,
                )
                await meta.add_item_note(
                    conn=conn,
                    item=target_item,
                    key='copied_image_from',
                    value=str(child.uuid),
                )
                changed = True
                total += 1

            if verbose and not changed:
                LOG.warning('Got no valid image sources for {}', target_item)

    return total


async def get_items_without_images(
    conn: AsyncConnection,
    only_users: list[UUID] | None,
    only_items: list[UUID] | None,
    limit: int | None,
) -> list[tuple[UUID, str, str | None]]:
    """Return all items without images."""
    query = (
        sa.select(
            db_models.Item.uuid,
            db_models.Item.name,
            db_models.ItemNote.value,
        )
        .where(
            sa.or_(
                db_models.Item.content_ext == sa.null(),
                db_models.Item.preview_ext == sa.null(),
                db_models.Item.thumbnail_ext == sa.null(),
            ),
            sa.or_(
                db_models.ItemNote.key == sa.null(),
                db_models.ItemNote.key == 'copied_image_from',
            ),
        )
        .join(
            db_models.ItemNote,
            db_models.ItemNote.item_id == db_models.Item.id,
            isouter=True,
        )
    )

    if only_users is not None:
        query = query.where(db_models.Item.owner_uuid.in_(only_users))

    if only_items is not None:
        query = query.where(db_models.Item.uuid.in_(only_items))

    if limit is not None:
        query = query.limit(limit)

    response = (await conn.execute(query)).fetchall()

    return [(row.uuid, row.name, row.value) for row in response]
