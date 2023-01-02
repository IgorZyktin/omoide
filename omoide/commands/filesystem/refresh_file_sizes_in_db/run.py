# -*- coding: utf-8 -*-
"""Refresh size command.
"""

from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.orm import Session

from omoide import infra
from omoide.commands.common import helpers
from omoide.commands.common.base_db import BaseDatabase
from omoide.commands.filesystem.refresh_file_sizes_in_db.cfg import Config
from omoide.infra import custom_logging
from omoide.storage.database import models

LOG = custom_logging.get_logger(__name__)


def run(
        database: BaseDatabase,
        config: Config,
) -> None:
    """Refresh disk usage for every item."""
    if Path(config.hot_folder).exists():
        path = config.hot_folder

    elif Path(config.cold_folder).exists():
        path = config.cold_folder

    else:
        raise RuntimeError(
            'No actual folder to work with '
            '(give hot or cold folder path)'
        )

    verbose_config = [
        f'\t{key}={value},\n'
        for key, value in config.dict().items()
    ]
    LOG.info(f'Config:\n{{\n{"".join(verbose_config)}}}')

    with Session(database.engine) as session:
        users = helpers.get_all_corresponding_users(
            session=session,
            only_user=config.only_user,
        )

    local_changed = 0
    total_changed = 0
    last_meta = None

    with Session(database.engine) as session:
        for user in users:
            i = 0
            LOG.info('Refreshing file sizes for user {}', user.name)
            models_for_user = get_models(session, config, user)
            print(models_for_user)
            for i, (metainfo, item) in enumerate(models_for_user, start=1):
                operations = update_size(config, metainfo, item, path)
                session.commit()
                local_changed += operations
                total_changed += operations
                last_meta = metainfo.item_uuid

                if config.log_every_item:
                    if operations:
                        LOG.info('Changed item N{} {} {} ({} operations)',
                                 i, item.uuid, item.name, operations)
                    else:
                        LOG.info('Nothing changed for item N{} {} {}',
                                 i, item.uuid, item.name)

            local_changed = 0
            LOG.info('Changed {} items for user {} ({} operations)',
                     i, user.name, local_changed)

        LOG.warning('Last record: {}', last_meta)


def update_size(
        config: Config,
        metainfo: models.Metainfo,
        item: models.Item,
        base_folder: str,
) -> int:
    """Get actual file size."""
    locator = infra.FilesystemLocator(
        base_folder=base_folder,
        item=item,
        prefix_size=config.prefix_size,
    )

    changed = 0
    for each in ['content', 'preview', 'thumbnail']:
        ext = getattr(item, f'{each}_ext')
        if ext:
            path = getattr(locator, each)
            size = helpers.get_file_size(path)

            if size is not None:
                setattr(metainfo, f'{each}_size', size)
                changed += 1

    return changed


def get_models(
        session: Session,
        config: Config,
        user: models.User,
) -> list[tuple[models.Metainfo, models.Item]]:
    """Get every item with some content."""
    query = session.query(
        models.Metainfo,
        models.Item,
    ).join(
        models.Item,
        models.Item.uuid == models.Metainfo.item_uuid,
    ).filter(
        models.Item.owner_uuid == user.uuid,
        sa.or_(
            sa.and_(
                models.Item.content_ext != None,  # noqa
                models.Metainfo.content_size == None,  # noqa
            ),
            sa.and_(
                models.Item.preview_ext != None,  # noqa
                models.Metainfo.preview_size == None,  # noqa
            ),
            sa.and_(
                models.Item.thumbnail_ext != None,  # noqa
                models.Metainfo.thumbnail_size == None,  # noqa
            ),
        ),
    )

    if config.marker:
        query = query.filter(
            models.Metainfo.uuid >= config.marker  # noqa
        )

    query = query.order_by(
        models.Metainfo.item_uuid,
    )

    if config.limit != -1:
        query = query.limit(config.limit)

    return query.all()
