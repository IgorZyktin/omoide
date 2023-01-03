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
            top_item = get_item(session, user.root_item)

            local_operations = 0
            if top_item is not None:
                local_operations += copy_labeled_items(session, top_item)
                local_operations += copy_from_deep(session, top_item)
                total_operations += local_operations

                if local_operations:
                    session.commit()

    LOG.info('Total operations: {}', total_operations)


def copy_labeled_items(
        session: Session,
        item: models.Item,
) -> int:
    """Copy data for items with explicit origin."""
    metainfo = get_metainfo(session, item)
    copied_from = metainfo.extras.get('copied_cover_from')

    local_total = 0
    if copied_from:
        origin = get_item(session, copied_from)

        if origin:
            changes = copy_cover(
                session=session,
                source_item=origin,
                target_item=item,
            )
            local_total += changes

    return local_total


def copy_from_deep(
        session: Session,
        item: models.Item,
) -> int:
    """Copy data for items without explicit origins."""


# def force_to_copy(
#         session: Session,
#         config: Config,
#         user: models.User,
#         item: models.Item,
# ) -> int:
#     """Recursively dig into items and copy covers."""
#     metainfo = get_metainfo(session, item)
#     total_operations = 0
#
#     if has_all_the_data(item, metainfo):
#         changed = copy_cover(session, item, top_item)
#         total_operations += changed
#
#     s_depth = '\n' * depth
#     children = get_children(session, user, item)
#
#     if not children:
#         return 0
#
#     for child in children:
#         metainfo = get_metainfo(session, child)
#
#         if has_all_the_data(child, metainfo):
#             changed = copy_cover(session, item, child)
#             total_operations += changed
#
#             first_appropriate_child = find_closest_cover(
#                 session=session,
#                 user=user,
#                 item=child,
#                 top_level_item=child,
#             )
#
#             if first_appropriate_child is None:
#                 LOG.warning('{}Item {} has nothing to copy from',
#                             s_depth, child)
#                 continue
#
#             if config.log_every_item:
#                 LOG.info(
#                     '{}Copying cover from item {} to {}',
#                     s_depth,
#                     repr(first_appropriate_child),
#                     repr(child),
#                 )
#
#                 changed = copy_cover(
#                     session=session,
#                     source_item=first_appropriate_child,
#                     target_item=child,
#                 )
#                 total_operations += changed
#
#         changed = force_to_copy(
#             session=session,
#             config=config,
#             user=user,
#             item=child,
#             depth=depth + 1,
#         )
#         total_operations += changed
#
#     return total_operations


def get_item(
        session: Session,
        item_uuid: str | UUID,
) -> Optional[models.Item]:
    """Get item but only if it is collection."""
    if item_uuid is None:
        return None

    query = session.query(
        models.Item
    ).where(
        models.Item.uuid == str(item_uuid),
    )

    return query.first()


def get_children(
        session: Session,
        user: models.User,
        item: models.Item,
) -> list[models.Item]:
    """Get child items."""
    query = session.query(
        models.Item
    ).where(
        models.Item.parent_uuid == item.uuid,
        models.Item.owner_uuid == user.uuid,
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


def get_lowest_good_item(
        session: Session,
        user: models.User,
        item: models.Item,
) -> Optional[models.Item]:
    """Find deepest item with all data present."""
    metainfo = get_metainfo(session, item)

    if metainfo is None:
        LOG.error('Item {} has not metainfo', item)
        return None


#     copied_from = metainfo.extras.get('copied_cover_from')
#
#     # what if we already have good candidate?
#     if copied_from:
#         source_item = get_item(session, UUID(copied_from))
#         source_metainfo = get_metainfo(session, item)
#         if has_all_the_data(source_item, source_metainfo):
#             return source_item
#
#     children = get_children(session, user, item)
#
#     for child in children:
#         child_metainfo = get_metainfo(session, child)
#         if has_all_the_data(child, child_metainfo):
#             return child
#
#         else:
#             sub_child = find_closest_cover(
#                 session=session,
#                 user=user,
#                 item=child,
#                 top_level_item=top_level_item,
#             )
#
#             if sub_child is None:
#                 continue
#
#             sub_child_metainfo = get_metainfo(session, sub_child)
#
#             if has_all_the_data(sub_child, sub_child_metainfo):
#                 return sub_child
#
#     return None


def has_all_the_data(
        item: Optional[models.Item],
        metainfo: Optional[models.Metainfo],
) -> bool:
    """Get child items but only if they are collection."""
    if item is None or metainfo is None:
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

    session.add(content_copy)
    session.add(preview_copy)
    session.add(thumbnail_copy)
    session.flush([content_copy, preview_copy, thumbnail_copy])

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
