# -*- coding: utf-8 -*-
"""Collection to force copying of covers.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from omoide import utils
from omoide.commands.application \
    .force_collections_to_copy_cover.cfg import Config
from omoide.commands.common import helpers
from omoide.commands.common.base_db import BaseDatabase
from omoide.infra import custom_logging
from omoide.storage.database import models

LOG = custom_logging.get_logger(__name__)
_METAINFO_CACHE: dict[UUID, models.Metainfo] = {}


def run(
        database: BaseDatabase,
        config: Config,
) -> None:
    """Show disk usage for users."""
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

    total_operations = 0
    for user in users:

        if user.root_item is None:
            continue

        with Session(database.engine) as session:
            LOG.info('Forcing to copy covers for user {} {}',
                     user.uuid, user.name)
            changes = force_whole_tree_to_copy(session, config, user)
            total_operations += changes
            session.commit()

    LOG.info('Total operations: {}', total_operations)


def force_whole_tree_to_copy(
        session: Session,
        config: Config,
        user: models.User,
) -> int:
    """Recursively dig into items and copy covers."""
    top_item = get_item(session, user.root_item)

    if top_item is None:
        return 0

    children = get_children(session, user, top_item, only_collections=True)

    if not children:
        return 0

    total_operations = 0

    for child in children:
        if has_all_the_data(child):
            continue

        first_appropriate_child = find_closest_cover(
            session=session,
            user=user,
            item=child,
            top_level_item=child,
        )

        if config.log_every_item:
            LOG.info(
                '\tCopying cover from item {} to {}',
                repr(first_appropriate_child),
                repr(child),
            )

            total_operations += copy_cover(
                session=session,
                source_item=first_appropriate_child,
                target_item=child,
            )

    return total_operations


def get_item(
        session: Session,
        item_uuid: Optional[UUID],
) -> Optional[models.Item]:
    """Get item but only if it is collection."""
    if item_uuid is None:
        return None

    query = session.query(
        models.Item
    ).where(
        models.Item.uuid == str(item_uuid),
        models.Item.is_collection == True,  # noqa
    )

    return query.first()


def get_children(
        session: Session,
        user: models.User,
        item: models.Item,
        only_collections: bool,
) -> list[models.Item]:
    """Get child items but only if they are collection."""
    query = session.query(
        models.Item
    ).where(
        models.Item.parent_uuid == item.uuid,
        models.Item.owner_uuid == user.uuid,
    )

    if only_collections:
        query = query.filter(
            models.Item.is_collection == True,  # noqa
        )

    query = query.order_by(
        models.Item.number
    )

    return query.all()


def get_metainfo(
        session: Session,
        item: models.Item,
) -> Optional[models.Metainfo]:
    """Get cached metainfo for given item."""
    cached = _METAINFO_CACHE.get(item.uuid)

    if cached is not None:
        return cached

    metainfo = session.query(
        models.Metainfo
    ).where(
        models.Metainfo.item_uuid == item.uuid
    ).first()

    _METAINFO_CACHE[item.uuid] = metainfo

    return metainfo


def find_closest_cover(
        session: Session,
        user: models.User,
        item: models.Item,
        top_level_item: models.Item,
) -> Optional[models.Item]:
    """Get first child with acceptable cover."""
    # if item itself is good
    if has_all_the_data(item):
        return item

    metainfo = get_metainfo(session, item)

    if metainfo is None:
        return None

    source_uuid = metainfo.extras.get('copied_cover_from')

    if source_uuid:
        source_item = get_item(session, UUID(source_uuid))
        if has_all_the_data(source_item):
            return source_item

    children = get_children(session, user, item, only_collections=False)

    for child in children:
        if has_all_the_data(child):
            return child

        else:
            sub_child = find_closest_cover(
                session=session,
                user=user,
                item=child,
                top_level_item=top_level_item,
            )

            if has_all_the_data(sub_child):
                return sub_child

    return None


def has_all_the_data(
        item: Optional[models.Item],
) -> bool:
    """Get child items but only if they are collection."""
    if item is None:
        return False

    if all((
            item.content_ext != None,  # noqa
            item.preview_ext != None,  # noqa
            item.thumbnail_ext != None,  # noqa
    )):
        return True

    return False


def copy_cover(
        session: Session,
        source_item: models.Item,
        target_item: models.Item,
) -> int:
    """Get first child with acceptable cover."""
    metainfo = get_metainfo(session, target_item)

    if metainfo is None:
        return 0

    now = utils.now()

    content_copy = models.ManualCopy(
        created_at=now,
        processed_at=None,
        status='init',
        error='',
        owner_uuid=str(source_item.owner_uuid),
        source_uuid=str(source_item.uuid),
        target_uuid=str(target_item.uuid),
        ext=source_item.content_ext,
        target_folder='content',
    )

    preview_copy = models.ManualCopy(
        created_at=now,
        processed_at=None,
        status='init',
        error='',
        owner_uuid=str(source_item.owner_uuid),
        source_uuid=str(source_item.uuid),
        target_uuid=str(target_item.uuid),
        ext=source_item.preview_ext,
        target_folder='preview',
    )

    thumbnail_copy = models.ManualCopy(
        created_at=now,
        processed_at=None,
        status='init',
        error='',
        owner_uuid=str(source_item.owner_uuid),
        source_uuid=str(source_item.uuid),
        target_uuid=str(target_item.uuid),
        ext=source_item.thumbnail_ext,
        target_folder='thumbnail',
    )

    session.add_all([content_copy, preview_copy, thumbnail_copy])

    metainfo.extras.update({'copied_cover_from': str(source_item.uuid)})
    metainfo.updated_at = now
    flag_modified(metainfo, 'extras')

    total_operations = 0

    if not target_item.content_ext:
        total_operations += 1

    if not target_item.preview_ext:
        total_operations += 1

    if not target_item.thumbnail_ext:
        total_operations += 1

    return total_operations
