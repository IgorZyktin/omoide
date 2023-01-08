# -*- coding: utf-8 -*-
"""Collection to force copying of covers.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from omoide import domain
from omoide import utils
from omoide.commands.application.force_cover_copying.cfg import Config
from omoide.commands.common import helpers
from omoide.commands.common.base_db import BaseDatabase
from omoide.infra import custom_logging
from omoide.storage.database import models

LOG = custom_logging.get_logger(__name__)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

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

    with database.start_session() as session:
        users = helpers.get_all_corresponding_users(session, config.only_users)

    total_operations = 0

    for user in users:
        if user.root_item is None:
            continue

        LOG.info('Copying covers for user {} {}', user.uuid, user.name)

        with database.start_session() as session:
            already_handled: set[UUID] = set()
            leaf_items = get_leaf_items(session, user)

            changed = 0
            for item in leaf_items:
                changed += force_copy_to_all_parents(
                    session, item, already_handled)
                total_operations += changed
            LOG.info('Changed {} items', changed)
            session.commit()

    LOG.info('Total operations: {}', total_operations)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


def get_leaf_items(
        session: Session,
        user: models.User,
) -> list[models.Item]:
    """Get all items without children."""
    stmt = """
    SELECT *
    FROM items AS leaf
    LEFT OUTER JOIN items AS child on child.parent_uuid = leaf.uuid
    WHERE child.uuid IS NULL and leaf.owner_uuid = :user_uuid
    AND leaf.content_ext IS NOT NULL
    AND leaf.preview_ext IS NOT NULL
    AND leaf.thumbnail_ext IS NOT NULL
    ORDER BY leaf.number
    """

    values = {
        'user_uuid': str(user.uuid),
    }

    response = session.execute(stmt, values).fetchall()

    return [
        models.Item(
            uuid=x[0],
            parent_uuid=x[1],
            owner_uuid=x[2],
            number=x[3],
            name=x[4],
            is_collection=x[5],
            content_ext=x[6],
            preview_ext=x[7],
            thumbnail_ext=x[8],
            tags=x[9],
            permissions=x[10],
        )
        for x in response
    ]


def force_copy_to_all_parents(
        session: Session,
        item: models.Item,
        already_handled: set[UUID],
) -> int:
    """Copy data from given item to all parents."""
    changed = 0
    leaf_metainfo = helpers.get_metainfo(session, item)
    parent_uuid = item.parent_uuid

    while parent_uuid is not None:
        parent = helpers.get_item(session, parent_uuid)
        parent_metainfo = helpers.get_metainfo(session, item)

        if parent.uuid not in already_handled:
            copy_properties(
                session, parent, parent_metainfo, item, leaf_metainfo)
            invoke_worker_to_copy(
                session, parent, item)
            already_handled.add(parent.uuid)
            changed += 1

        parent_uuid = parent.parent_uuid

    return changed


def copy_properties(
        session: Session,
        parent: models.Item,
        parent_metainfo: models.Metainfo,
        child: models.Item,
        child_metainfo: models.Metainfo,
) -> None:
    """Copy basic parameters."""
    parameters_items = [
        'content_ext',
        'preview_ext',
        'thumbnail_ext',
    ]

    for parameter in parameters_items:
        setattr(parent, parameter,
                getattr(child, parameter))

    parameters_metainfo = [
        'media_type',

        'content_size',
        'preview_size',
        'thumbnail_size',

        'content_width',
        'content_height',

        'preview_width',
        'preview_height',

        'thumbnail_width',
        'thumbnail_height',
    ]

    for parameter in parameters_metainfo:
        setattr(parent_metainfo, parameter,
                getattr(child_metainfo, parameter))

    helpers.insert_into_metainfo_extras(
        session=session,
        metainfo=parent_metainfo,
        new_data={domain.COPIED_COVER_FROM: str(child.uuid)}
    )

    parent_metainfo.updated_at = utils.now()


def invoke_worker_to_copy(
        session: Session,
        parent: models.Item,
        child: models.Item,
) -> None:
    """Write info in the db so worker could complete the job."""
    now = utils.now()

    for media_type in domain.MEDIA_TYPES:
        ext = getattr(child, f'{media_type}_ext')
        assert ext is not None

        copy = models.ManualCopy(
            created_at=now,
            processed_at=None,
            status='init',
            error='',
            owner_uuid=parent.owner_uuid,
            source_uuid=child.uuid,
            target_uuid=parent.uuid,
            ext=ext,
            target_folder=media_type,
        )
        session.add(copy)
        session.flush([copy])
