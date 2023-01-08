# -*- coding: utf-8 -*-
"""Rebuild all content/preview/thumbnail sizes.
"""
import time
from typing import Optional
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from omoide import utils
from omoide.commands.application.rebuild_computed_tags.cfg import Config
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
    """Execute command."""
    verbose_config = [
        f'\t{key}={value},\n'
        for key, value in config.dict().items()
    ]
    LOG.info(f'Config:\n{{\n{"".join(verbose_config)}}}')

    with database.start_session() as session:
        users = helpers.get_all_corresponding_users(session, config.only_users)

    for user in users:
        LOG.info('Refreshing tags for user {} {}', user.uuid, user.name)

        with database.start_session() as session:
            start = time.perf_counter()
            children = rebuild_computed_tags(session, config, user)
            spent = time.perf_counter() - start
            LOG.info(
                'Rebuilt computed tags for '
                '{} {} ({} children) in {:0.3f} sec.',
                user.uuid,
                user.name,
                utils.sep_digits(children),
                spent,
            )
            session.commit()


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def rebuild_computed_tags(
        session: Session,
        config: Config,
        user: models.User,
) -> int:
    """Rebuild computed tags for specific user."""
    if user.root_item is None:
        return 0

    i = 0
    total_children = 0

    def recursive(parent_uuid: UUID) -> None:
        nonlocal i, total_children
        child_items = helpers.get_direct_children(session, parent_uuid)
        for child in child_items:
            i += 1
            total_children += 1
            tags = get_new_computed_tags(session, parent_uuid, child)
            insert_new_computed_tags(session, child, tags)

            if config.log_every_item:
                LOG.info(
                    '\t\tRefreshed tags for {}. {} {} {} {}',
                    utils.sep_digits(i),
                    child.uuid,
                    child.name or '???',
                    utils.sep_digits(total_children),
                    sorted(tags),
                )

            recursive(child.uuid)

    recursive(user.root_item)

    return total_children


def get_new_computed_tags(
        session: Session,
        parent_uuid: UUID,
        child: models.Item,
) -> tuple[str, ...]:
    """Refresh computed tags for given child."""
    parent_tags = session.query(
        models.ComputedTags.tags
    ).filter(
        models.ComputedTags.item_uuid == parent_uuid,
    ).scalar()

    child_tags = session.query(
        models.ComputedTags.tags
    ).filter(
        models.ComputedTags.item_uuid == child.uuid
    ).scalar()

    tags: tuple[str, ...] = gather_tags(
        parent_uuid=parent_uuid,
        parent_tags=parent_tags if parent_tags else [],
        item_uuid=child.uuid,
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
        session: Session,
        item: models.Item,
        tags: tuple[str, ...],
) -> None:
    """Forcefully insert new tags."""
    insert = pg_insert(
        models.ComputedTags
    ).values(
        item_uuid=item.uuid,
        tags=tuple(tags),
    )

    stmt = insert.on_conflict_do_update(
        index_elements=[models.ComputedTags.item_uuid],
        set_={
            'tags': insert.excluded.tags,
        }
    )

    session.execute(stmt)
