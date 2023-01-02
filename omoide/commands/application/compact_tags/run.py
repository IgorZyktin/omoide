# -*- coding: utf-8 -*-
"""Compact tags.
"""
import time

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased

from omoide import utils
from omoide.commands.application.compact_tags import cfg
from omoide.commands.application.compact_tags.cfg import Config
from omoide.commands.common import helpers
from omoide.commands.common.base_db import BaseDatabase
from omoide.infra import custom_logging
from omoide.storage.database import models

LOG = custom_logging.get_logger(__name__)


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

    with Session(database.engine) as session:
        users = helpers.get_all_corresponding_users(
            session=session,
            only_user=config.only_user,
        )

    for user in users:
        LOG.info('Compacting tags for {} {}', user.uuid, user.name)

        with database.start_session() as session:
            start = time.perf_counter()
            children = compact_tags(session, config, user)
            spent = time.perf_counter() - start

            LOG.info(
                'Compacted tags for '
                '{} (with {} children) in {:0.3f} sec.',
                user.name,
                utils.sep_digits(children),
                spent,
            )


def compact_tags(
        session: Session,
        config: cfg.Config,
        user: models.User,
) -> int:
    """Compact tags for given user."""
    total_items = 0

    alias = aliased(models.Item)

    query = session.query(
        models.Item,
        models.ComputedTags,
    ).join(
        models.ComputedTags,
        models.ComputedTags.item_uuid == models.Item.parent_uuid,
    ).filter(
        models.Item.owner_uuid == user.uuid
    ).filter(
        models.ComputedTags.tags.overlap(
            sa.select(
                sa.func.string_to_array(
                    sa.func.lower(
                        sa.func.array_to_string(models.Item.tags, '|'),
                    ), '|')
            ).where(
                alias.uuid == models.ComputedTags.item_uuid
            ).scalar_subquery()
        )
    ).order_by(
        models.Item.number
    )

    for item, computed_tags in query.all():
        lower = {tag.lower() for tag in computed_tags.tags}
        can_drop = {tag for tag in item.tags if tag.lower() in lower}

        if config.log_every_item:
            LOG.info(
                'Compacting {}, dropping {} for item {} {}',
                item.uuid,
                sorted(can_drop),
                item.uuid,
                item.name,
            )

        item.tags = [tag for tag in item.tags if tag not in can_drop]

        for tag in can_drop:
            known_tag = session.query(
                models.KnownTags
            ).filter(
                models.KnownTags.user_uuid == user.uuid,
                models.KnownTags.tag == tag,
            ).first()

            if known_tag:
                known_tag.counter -= 1
            elif config.log_every_item:
                LOG.warning('Tag {} does not exist', tag)

        total_items += 1

    session.query(
        models.KnownTags
    ).filter(
        models.KnownTags.counter <= 0
    ).delete()

    session.commit()

    return total_items
