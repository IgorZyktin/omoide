"""Rebuild all computed tags from the scratch.
"""
import time
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection

from omoide import utils
from omoide.commands import helpers
from omoide.commands.rebuild_computed_tags.cfg import Config
from omoide.infra import custom_logging
from omoide.storage.database import db_models
from omoide.storage.database import sync_db

LOG = custom_logging.get_logger(__name__)


def run(config: Config, database: sync_db.SyncDatabase) -> None:
    """Execute command."""
    LOG.info('\nConfig:\n{}', utils.serialize_model(config))

    with database.start_session() as session:
        users = helpers.get_all_corresponding_users(session, config.only_users)

    for user in users:
        LOG.info('Refreshing tags for user {} {}', user.uuid, user.name)

        with database.start_transaction() as conn:
            start = time.perf_counter()
            children = rebuild_computed_tags(conn, config, user)
            spent = time.perf_counter() - start
            LOG.info(
                'Rebuilt computed tags for '
                '{} {} ({} children) in {:0.3f} sec.',
                user.uuid,
                user.name,
                utils.sep_digits(children),
                spent,
            )


def rebuild_computed_tags(
        conn: Connection,
        config: Config,
        user: db_models.User,
) -> int:
    """Rebuild computed tags for specific user."""
    if user.root_item is None:
        return 0

    i = 0
    total_children = 0

    def recursive(parent_uuid: UUID) -> None:
        nonlocal i, total_children
        child_items = get_direct_children(conn, parent_uuid)
        for child_uuid, child_name in child_items:
            i += 1
            total_children += 1
            tags = get_new_computed_tags(conn, parent_uuid, child_uuid)
            insert_new_computed_tags(conn, child_uuid, tags)

            if config.log_every_item:
                LOG.info(
                    '\t\tRefreshed tags for {}. {} {} {} {}',
                    utils.sep_digits(i),
                    child_uuid,
                    child_name or '???',
                    utils.sep_digits(total_children),
                    sorted(tags),
                )

            recursive(child_uuid)

    recursive(user.root_item)

    return total_children


def get_direct_children(
        conn: Connection,
        uuid: UUID,
) -> list[tuple[UUID, str]]:
    """Return all direct children."""
    stmt = sa.select(
        db_models.Item.uuid,
        db_models.Item.name,
    ).where(
        db_models.Item.parent_uuid == uuid
    ).order_by(
        db_models.Item.number
    )
    return cast(list[tuple[UUID, str]], conn.execute(stmt).fetchall())


def get_new_computed_tags(
        conn: Connection,
        parent_uuid: UUID,
        child_uuid: UUID,
) -> tuple[str, ...]:
    """Refresh computed tags for given child."""
    stmt = sa.select(
        db_models.ComputedTags.tags
    ).where(
        db_models.ComputedTags.item_uuid == parent_uuid
    )
    parent_tags = conn.execute(stmt).scalar()

    stmt = sa.select(
        db_models.ComputedTags.tags
    ).where(
        db_models.ComputedTags.item_uuid == child_uuid
    )
    child_tags = conn.execute(stmt).scalar()

    tags: tuple[str, ...] = gather_tags(
        parent_uuid=parent_uuid,
        parent_tags=parent_tags if parent_tags else [],
        item_uuid=child_uuid,
        item_tags=child_tags if child_tags else [],
    )

    return tags


def gather_tags(
        parent_uuid: UUID,
        parent_tags: list[str],
        item_uuid: UUID,
        item_tags: list[str],
) -> tuple[str, ...]:
    """Combine parent tags with item tags."""
    clean_parent_uuid = str(parent_uuid).lower()

    all_tags = {
        *(x.lower() for x in parent_tags if x != clean_parent_uuid),
        *(x.lower() for x in item_tags),
        str(item_uuid),
    }

    return tuple(all_tags)


def insert_new_computed_tags(
        conn: Connection,
        item_uuid: UUID,
        tags: tuple[str, ...],
) -> None:
    """Forcefully insert new tags."""
    insert = pg_insert(
        db_models.ComputedTags
    ).values(
        item_uuid=item_uuid,
        tags=tuple(tags),
    )

    stmt = insert.on_conflict_do_update(
        index_elements=[db_models.ComputedTags.item_uuid],
        set_={'tags': insert.excluded.tags}
    )

    conn.execute(stmt)
