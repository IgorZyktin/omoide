"""Refresh size command.
"""
from pathlib import Path
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from omoide import domain
from omoide import const
from omoide import infra
from omoide import utils
from omoide.commands import helpers
from omoide.commands.refresh_file_sizes_in_db.cfg import Config
from omoide import custom_logging
from omoide.storage.database import db_models
from omoide.storage.database.sync_db import SyncDatabase

LOG = custom_logging.get_logger(__name__)


def run(config: Config, database: SyncDatabase) -> None:
    """Refresh disk usage for every item."""
    LOG.info('\nConfig:\n{}', utils.serialize_model(config))

    if config.hot_folder and Path(config.hot_folder).exists():
        path = config.hot_folder

    elif config.cold_folder and Path(config.cold_folder).exists():
        path = config.cold_folder

    else:
        msg = 'No actual folder to work with (give hot or cold folder path)'
        raise RuntimeError(msg)

    with database.start_session() as session:
        users = helpers.get_all_corresponding_users(session, config.only_users)

    i = 0
    local_changed = 0
    total_changed = 0
    last_meta = None

    for user in users:
        with database.start_session() as session:
            LOG.info('Refreshing file sizes for user {} {}',
                     user.uuid, user.name)

            models_for_user = get_models(session, config, user)

            LOG.info('Checking {} models',
                     utils.sep_digits(len(models_for_user)))

            for i, (metainfo, item) in enumerate(models_for_user, start=1):
                operations = update_size(config, metainfo, item, path)
                local_changed += operations
                total_changed += operations
                last_meta = metainfo.item_uuid

                if config.log_every_item:
                    if operations:
                        LOG.info('\t\tChanged item {} {} ({} operations)',
                                 item.uuid, item.name, operations)

                if operations:
                    session.commit()

            if local_changed:
                LOG.info('\tChanged {} items for user {} ({} operations)',
                         i, user.name, local_changed)

            local_changed = 0

    LOG.info('Total changes: {}', utils.sep_digits(total_changed))
    LOG.warning('Last record: {}', last_meta)


def update_size(
        config: Config,
        metainfo: db_models.Metainfo,
        item: db_models.Item,
        base_folder: str,
) -> int:
    """Get actual file size."""
    dom_item = domain.Item(
        uuid=item.uuid,
        parent_uuid=item.parent_uuid,
        owner_uuid=item.owner_uuid,
        number=item.number,
        name=item.name,
        is_collection=item.is_collection,
        content_ext=item.content_ext,
        preview_ext=item.preview_ext,
        thumbnail_ext=item.thumbnail_ext,
        tags=item.tags,
        permissions=[UUID(x) for x in item.permissions],  # type: ignore
    )

    locator = infra.FilesystemLocator(
        base_folder=base_folder,
        item=dom_item,
        prefix_size=config.prefix_size,
    )

    changed = 0
    for media_type in const.MEDIA_TYPES:
        ext = getattr(item, f'{media_type}_ext', None)

        if not ext:
            LOG.error('No {} extension for {}, skipping', media_type, item)
            continue

        path = getattr(locator, media_type)
        size = helpers.get_file_size(path)

        if size is None:
            LOG.error('File does not exist for {}: {}', item.uuid, path)
            continue

        if size == getattr(metainfo, f'{media_type}_size', None):
            continue

        setattr(metainfo, f'{media_type}_size', size)
        metainfo.updated_at = utils.now()
        changed += 1

    return changed


def get_models(
        session: Session,
        config: Config,
        user: db_models.User,
) -> list[tuple[db_models.Metainfo, db_models.Item]]:
    """Get every item with some content."""
    query = session.query(
        db_models.Metainfo,
        db_models.Item,
    ).join(
        db_models.Item,
        db_models.Item.uuid == db_models.Metainfo.item_uuid,
    ).filter(
        db_models.Item.owner_uuid == user.uuid,
        sa.or_(
            db_models.Metainfo.content_size == None,  # noqa
            db_models.Metainfo.preview_size == None,  # noqa
            db_models.Metainfo.thumbnail_size == None,  # noqa
        ),
    )

    if config.marker:
        query = query.filter(
            db_models.Metainfo.item_uuid >= config.marker  # noqa
        )

    query = query.order_by(
        db_models.Metainfo.item_uuid,
    )

    if config.limit != -1:
        query = query.limit(config.limit)

    return query.all()
