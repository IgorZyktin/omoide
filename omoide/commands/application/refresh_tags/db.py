# -*- coding: utf-8 -*-
"""Database helpers.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from omoide import utils
from omoide.commands.application.refresh_tags.cfg import Config
from omoide.commands.common.base_db import BaseDatabase
from omoide.infra import custom_logging
from omoide.storage.database import models

LOG = custom_logging.get_logger(__name__)


def get_users(database: BaseDatabase) -> list[models.User]:
    """Get all registered users."""
    with database.start_session() as session:
        return session.query(models.User).order_by(models.User.name).all()


def get_user(database: BaseDatabase, uuid: UUID) -> Optional[models.User]:
    """Get specific registered users."""
    with database.start_session() as session:
        return session.query(models.User).get(str(uuid))


# Functions for known users ---------------------------------------------------

def get_direct_children(session: Session, uuid: UUID) -> list[models.Item]:
    """Return all direct children."""
    return session.query(
        models.Item
    ).filter(
        models.Item.parent_uuid == uuid
    ).order_by(
        models.Item.number
    ).all()


def gather_tags(
        parent_uuid: Optional[UUID],
        parent_tags: list[str],
        item_uuid: UUID,
        item_tags: list[str],
) -> tuple[str, ...]:
    """Combine parent tags with item tags."""
    all_tags = {
        *(x.lower() for x in item_tags),
        str(item_uuid),
    }

    if parent_uuid is not None:
        clean_parent_uuid = str(parent_uuid).lower()
        clean_tags = (
            lower
            for x in parent_tags
            if (lower := x.lower()) != clean_parent_uuid
        )
        all_tags.update(clean_tags)

    return tuple(all_tags)


def refresh_computed_tags(
        session: Session,
        parent_uuid: Optional[UUID],
        child: models.Item,
) -> list[str]:
    """Refresh computed tags for given child."""
    _tags: list[str] = []

    if parent_uuid is not None:
        parent_tags = session.query(models.ComputedTags).get(str(parent_uuid))

        if parent_tags is None:
            parent_tags = models.ComputedTags(item_uuid=parent_uuid, tags=[])
            session.add(parent_tags)
            session.commit()

        tags = gather_tags(
            parent_uuid=parent_uuid,
            parent_tags=list(str(x) for x in parent_tags.tags or []),
            item_uuid=child.uuid,
            item_tags=list(str(x) for x in child.tags or []),
        )

        child_tags = session.query(models.ComputedTags).get(str(child.uuid))

        if child_tags is None:
            child_tags = models.ComputedTags(
                item_uuid=child.uuid,
                tags=list(tags),
            )
        else:
            child_tags.tags = list(str(x) for x in tags)

        session.add(child_tags)
        session.commit()
        _tags.extend(list(str(x) for x in child_tags.tags or []))

    return _tags


def refresh_tags(
        config: Config,
        session: Session,
        user: models.User,
) -> int:
    """Refresh tags for the user."""
    total_children = 0

    if user.root_item is None:
        return total_children

    root_item = session.query(models.Item).get(str(user.root_item))

    if isinstance(root_item, models.Item):
        refresh_computed_tags(session, None, root_item)
    else:
        return total_children

    def recursive(_session: Session, parent_uuid: UUID) -> None:
        nonlocal total_children
        child_items = get_direct_children(_session, parent_uuid)
        for child in child_items:
            total_children += 1
            tags = refresh_computed_tags(_session, parent_uuid, child)

            if config.output_items:
                LOG.info('Refreshed tags for {}. {} {} {}',
                         utils.sep_digits(total_children),
                         child.uuid,
                         child.name or '???',
                         sorted(tags))

            recursive(_session, child.uuid)

    recursive(session, user.root_item)

    return total_children
