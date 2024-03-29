"""Compact tags.
"""
import time

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased

from omoide import utils
from omoide.commands.compact_tags import cfg
from omoide.commands.compact_tags.cfg import Config
from omoide.commands import helpers
from omoide.infra import custom_logging
from omoide.storage.database import db_models
from omoide.storage.database.sync_db import SyncDatabase

LOG = custom_logging.get_logger(__name__)


def run(config: Config, database: SyncDatabase) -> None:
    """Execute command."""
    LOG.info('\nConfig:\n{}', utils.serialize_model(config))

    with database.start_session() as session:
        users = helpers.get_all_corresponding_users(
            session=session,
            only_users=config.only_users,
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
        user: db_models.User,
) -> int:
    """Compact tags for given user."""
    total_items = 0

    alias = aliased(db_models.Item)

    query = session.query(
        db_models.Item,
        db_models.ComputedTags,
    ).join(
        db_models.ComputedTags,
        db_models.ComputedTags.item_uuid == db_models.Item.parent_uuid,
    ).filter(
        db_models.Item.owner_uuid == user.uuid
    ).filter(
        db_models.ComputedTags.tags.overlap(
            sa.select(
                sa.func.string_to_array(
                    sa.func.lower(
                        sa.func.array_to_string(db_models.Item.tags, '|'),
                    ), '|')
            ).where(
                alias.uuid == db_models.ComputedTags.item_uuid
            ).scalar_subquery()
        )
    ).order_by(
        db_models.Item.number
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
                db_models.KnownTags
            ).filter(
                db_models.KnownTags.user_uuid == user.uuid,
                db_models.KnownTags.tag == tag,
            ).first()

            if known_tag:
                known_tag.counter -= 1
            elif config.log_every_item:
                LOG.warning('Tag {} does not exist', tag)

        total_items += 1

    session.query(
        db_models.KnownTags
    ).filter(
        db_models.KnownTags.counter <= 0
    ).delete()

    session.commit()

    return total_items
