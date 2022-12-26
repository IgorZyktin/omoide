# -*- coding: utf-8 -*-
"""Database helpers.
"""
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased

from omoide.commands.application.compact_tags import cfg
from omoide.infra import custom_logging
from omoide.storage.database import models

LOG = custom_logging.get_logger(__name__)


def compact_tags(
        config: cfg.Config,
        session: Session,
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

        if config.output_items:
            LOG.info('Compacting {}, dropping {}',
                     item.uuid,
                     sorted(can_drop))

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
            else:
                LOG.warning('Tag {} does not exist', tag)

        total_items += 1

    session.query(
        models.KnownTags
    ).filter(
        models.KnownTags.counter <= 0
    ).delete()

    session.commit()

    return total_items
