# -*- coding: utf-8 -*-
"""Refresh cache for known tags.
"""
from collections import defaultdict
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from omoide import utils
from omoide.commands.application.rebuild_known_tags.cfg import Config
from omoide.commands.common import helpers
from omoide.commands.common.base_db import BaseDatabase
from omoide.infra import custom_logging
from omoide.storage.database import models

LOG = custom_logging.get_logger(__name__)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


def run(
        config: Config,
        database: BaseDatabase,
) -> None:
    """Execute command."""
    verbose_config = [
        f'\t{key}={value},\n'
        for key, value in config.dict().items()
    ]
    LOG.info(f'Config:\n{{\n{"".join(verbose_config)}}}')

    if config.anon and not config.only_users:
        with database.start_session() as session:
            set_all_tag_counters_to_zero(session, None)
            rebuild_tags_for_anon(session)

    if config.known:
        with database.start_session() as session:
            users = helpers.get_all_corresponding_users(
                session, config.only_users)

        for user in users:
            with database.start_session() as session:
                set_all_tag_counters_to_zero(session, user)
                rebuild_tags_for_known(session, user)

    drop_unused_tags(session)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


def get_public_users(session: Session) -> set[UUID]:
    """Return all public users."""
    stmt = sa.select(models.PublicUsers.user_uuid)
    response = session.execute(stmt)
    return set(x for x, in response.all())


def rebuild_tags_for_known(session: Session, user: models.User) -> None:
    """Rebuild tags for known user"""
    total_tags, occurrences = rebuild_known_tags_for_known_user(session, user)
    LOG.info(
        '{} (got {} tags with {} occurrences)',
        user.name,
        utils.sep_digits(total_tags),
        utils.sep_digits(occurrences),
    )


def rebuild_tags_for_anon(session: Session) -> None:
    """Rebuild tags for anon"""
    total_tags, occurrences = rebuild_known_tags_for_anon_user(session)
    LOG.info(
        'Anon (got {} tags with {} occurrences)',
        utils.sep_digits(total_tags),
        utils.sep_digits(occurrences),
    )


def drop_unused_tags(session: Session) -> None:
    """Delete all tags with counter less or equal zero."""
    stmt = sa.delete(
        models.KnownTags
    ).filter(
        models.KnownTags.counter <= 0
    )
    rowcount = session.execute(stmt).scalar()

    if rowcount:
        LOG.info('Dropped {} tags for known users', rowcount)

    stmt = sa.delete(
        models.KnownTagsAnon
    ).filter(
        models.KnownTagsAnon.counter <= 0
    )
    rowcount = session.execute(stmt).scalar()

    if rowcount:
        LOG.info('Dropped {} tags for anon user', rowcount)

    session.commit()


def set_all_tag_counters_to_zero(
        session: Session,
        user: Optional[models.User],
) -> None:
    """Mark all counters as 0, so we could start recalculating."""
    if user is None:
        stmt = sa.update(
            models.KnownTagsAnon
        ).values(
            counter=0
        )

    else:
        stmt = sa.update(
            models.KnownTags
        ).where(
            models.KnownTags.user_uuid == user.uuid
        ).values(
            counter=0
        )

    session.execute(stmt)
    session.commit()


def rebuild_known_tags_for_anon_user(
        session: Session,
) -> tuple[int, int]:
    """Refresh known tags for anon user (without dropping)."""
    total_count = 0
    occurrences = 0

    public_users = get_public_users(session)

    stmt = sa.select(
        models.Item.tags
    ).where(
        models.Item.owner_uuid.in_(tuple(public_users)),  # noqa
    )

    all_tags = session.execute(stmt)
    counters: dict[str, int] = defaultdict(int)

    for tag_group, in all_tags:
        occurrences += len(tag_group)
        for tag in tag_group:
            counters[str(tag).lower()] += 1
            total_count += 1

    for tag, counter in counters.items():
        insert = pg_insert(
            models.KnownTagsAnon
        ).values(
            tag=tag,
            counter=counter,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[
                models.KnownTagsAnon.tag,
            ],
            set_={
                'counter': insert.excluded.counter,
            }
        )
        session.execute(stmt)

    session.commit()

    return total_count, occurrences


def rebuild_known_tags_for_known_user(
        session: Session,
        user: models.User,
) -> tuple[int, int]:
    """Refresh known tags for known user (without dropping)."""
    total_count = 0
    occurrences = 0

    stmt = sa.select(
        models.Item.tags
    ).where(
        sa.or_(
            models.Item.owner_uuid == user.uuid,
            models.Item.permissions.contains([str(user.uuid)]),
        )
    )

    all_tags = [*session.execute(stmt)]
    counters: dict[str, int] = defaultdict(int)

    for tag_group, in all_tags:
        occurrences += len(tag_group)
        for tag in tag_group:
            counters[str(tag).lower()] += 1
            total_count += 1

    for tag, counter in counters.items():
        insert = pg_insert(
            models.KnownTags
        ).values(
            user_uuid=user.uuid,
            tag=tag,
            counter=counter,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[
                models.KnownTags.user_uuid,
                models.KnownTags.tag,
            ],
            set_={
                'counter': insert.excluded.counter,
            }
        )
        session.execute(stmt)

    session.commit()

    return total_count, occurrences
