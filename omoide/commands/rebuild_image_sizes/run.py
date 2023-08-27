"""Rebuild all content/preview/thumbnail sizes.
"""
import time

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import Session

from omoide import domain
from omoide import infra
from omoide import utils
from omoide.commands import helpers
from omoide.commands.rebuild_image_sizes.cfg import Config
from omoide.infra import custom_logging
from omoide.storage.database import db_models
from omoide.storage.database.sync_db import SyncDatabase

LOG = custom_logging.get_logger(__name__)


def run(config: Config, database: SyncDatabase) -> None:
    """Execute command."""
    LOG.info('\nConfig:\n{}', utils.serialize_model(config))

    if not (config.hot_folder or config.cold_folder):
        msg = 'No actual folder to work with (give hot or cold folder path)'
        raise RuntimeError(msg)

    with database.start_session() as session:
        users = helpers.get_all_corresponding_users(session, config.only_users)

    for user in users:
        with database.start_session() as session:
            start = time.perf_counter()
            all_metainfo = get_all_metainfo_records(session, config, user)

            if not all_metainfo:
                continue

            LOG.info('Refreshing image sizes for user {} {}',
                     user.uuid, user.name)

            rebuild_sizes(config, user, all_metainfo)
            spent = time.perf_counter() - start

            LOG.info(
                'Rebuilt image sizes for '
                '{} {} ({} records) in {:0.3f} sec.',
                user.uuid,
                user.name,
                utils.sep_digits(len(all_metainfo)),
                spent,
            )
            session.commit()


def get_all_metainfo_records(
        session: Session,
        config: Config,
        user: db_models.User,
) -> list[tuple[db_models.Metainfo, db_models.Item]]:
    """Rebuild computed tags for specific user."""
    query = session.query(
        db_models.Metainfo,
        db_models.Item,
    ).join(
        db_models.Item,
        db_models.Item.uuid == db_models.Metainfo.item_uuid,
    ).filter(
        db_models.Item.owner_uuid == user.uuid,
        ~sa.and_(
            db_models.Item.content_ext == None,  # noqa
            db_models.Item.preview_ext == None,  # noqa
            db_models.Item.thumbnail_ext == None,  # noqa
        ),
    )

    if config.only_corrupted:
        query = query.filter(
            sa.or_(
                db_models.Metainfo.content_width == None,  # noqa
                db_models.Metainfo.content_height == None,  # noqa
                db_models.Metainfo.preview_width == None,  # noqa
                db_models.Metainfo.preview_height == None,  # noqa
                db_models.Metainfo.thumbnail_width == None,  # noqa
                db_models.Metainfo.thumbnail_height == None,  # noqa
            )
        )

    query = query.order_by(
        db_models.Item.number
    )

    if config.limit > 0:
        query = query.limit(config.limit)

    result = query.all()

    return result


class Sizes(BaseModel):
    """DTO for image sizes."""
    content_width: int = -1
    content_height: int = -1
    preview_width: int = -1
    preview_height: int = -1
    thumbnail_width: int = -1
    thumbnail_height: int = -1


def rebuild_sizes(
        config: Config,
        user: db_models.User,
        all_metainfo: list[tuple[db_models.Metainfo, db_models.Item]],
) -> None:
    """Refresh computed tags for given child."""
    try:
        from PIL import Image
    except ImportError:
        Image = exit  # noqa
        LOG.error('You have to install "pillow" package to run this command')
        exit(1)

    for metainfo, item in all_metainfo:
        if metainfo is None or item is None:
            LOG.error('Failed to get data, metainfo={}, item={}',
                      metainfo, item)
            continue

        locator = make_locator(config, user, item)
        sizes = Sizes()

        for media_type in domain.MEDIA_TYPES:
            x_width = f'{media_type}_width'
            x_height = f'{media_type}_height'

            if all((
                    config.only_corrupted,
                    getattr(metainfo, x_width),
                    getattr(metainfo, x_height),
            )):
                continue

            ext = getattr(item, f'{media_type}_ext', None)

            if not ext:
                LOG.error('No {} extension for {}, skipping',
                          media_type, item)
                continue

            path = getattr(locator, media_type)
            try:
                size = Image.open(path).size
            except FileNotFoundError:
                size = None

            if not size:
                LOG.error('File does not exist for {}: {}',
                          item.uuid, path)
                continue

            width, height = size

            setattr(sizes, f'{media_type}_width', width)
            setattr(sizes, f'{media_type}_height', height)

            setattr(metainfo, f'{media_type}_width', width)
            setattr(metainfo, f'{media_type}_height', height)

        if config.log_every_item:
            LOG.info('Refreshed {}    {}', item.uuid, sizes)


def make_locator(
        config: Config,
        user: db_models.User,
        item: db_models.Item,
) -> infra.FilesystemLocator:
    """Make locator from pieces of item data."""
    dom_item = domain.Item(
        uuid=item.uuid,
        parent_uuid=item.parent_uuid,
        owner_uuid=user.uuid,
        number=item.number,
        name=item.name,
        is_collection=item.is_collection,
        content_ext=item.content_ext,
        preview_ext=item.preview_ext,
        thumbnail_ext=item.thumbnail_ext,
        tags=[],
        permissions=[],
    )

    locator = infra.FilesystemLocator(
        base_folder=config.hot_folder or config.cold_folder,
        item=dom_item,
        prefix_size=config.prefix_size,
    )

    return locator
