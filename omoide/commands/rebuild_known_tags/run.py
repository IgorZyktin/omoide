"""Refresh cache for known tags.
"""
from collections import defaultdict
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection

from omoide import utils
from omoide.commands import helpers
from omoide.commands.rebuild_known_tags.cfg import Config
from omoide import custom_logging
from omoide.storage.database import db_models
from omoide.storage.database import sync_db

LOG = custom_logging.get_logger(__name__)


def run(config: Config, database: sync_db.SyncDatabase) -> None:
    """Execute command."""
    LOG.info('\nConfig:\n{}', utils.serialize_model(config))

    if config.anon and not config.only_users:
        with database.start_transaction() as conn:
            set_all_tag_counters_to_zero_for_anon(conn)
            rebuild_tags_for_anon(conn)

    if config.known:
        with database.start_session() as session:
            users = helpers.get_all_corresponding_users(
                session, config.only_users)

        for user in users:
            with database.start_transaction() as conn:
                set_all_tag_counters_to_zero(conn, user)
                rebuild_tags_for_known(conn, user)

    with database.start_transaction() as conn:
        drop_unused_tags(conn)


def get_public_users(conn: Connection) -> set[UUID]:
    """Return all public users."""
    stmt = sa.select(db_models.PublicUsers.user_uuid)
    response = conn.execute(stmt)
    return set(x for x, in response.all())


def rebuild_tags_for_known(conn: Connection, user: db_models.User) -> None:
    """Rebuild tags for known user"""
    total_tags, occurrences = rebuild_known_tags_for_known_user(conn, user)
    LOG.info(
        '{} (got {} tags with {} occurrences)',
        user.name,
        utils.sep_digits(total_tags),
        utils.sep_digits(occurrences),
    )


def rebuild_tags_for_anon(conn: Connection) -> None:
    """Rebuild tags for anon"""
    total_tags, occurrences = rebuild_known_tags_for_anon_user(conn)
    LOG.info(
        'Anon (got {} tags with {} occurrences)',
        utils.sep_digits(total_tags),
        utils.sep_digits(occurrences),
    )


def drop_unused_tags(conn: Connection) -> None:
    """Delete all tags with counter less or equal zero."""
    stmt = sa.delete(
        db_models.KnownTags
    ).where(
        db_models.KnownTags.counter <= 0
    )
    response = conn.execute(stmt)

    if response.rowcount:
        LOG.info('Dropped {} tags for known users', response.rowcount)

    stmt = sa.delete(
        db_models.KnownTagsAnon
    ).filter(
        db_models.KnownTagsAnon.counter <= 0
    )
    response = conn.execute(stmt)

    if response.rowcount:
        LOG.info('Dropped {} tags for anon user', response.rowcount)


def set_all_tag_counters_to_zero_for_anon(conn: Connection) -> None:
    """Mark all counters as 0, so we could start recalculating."""
    stmt = sa.update(
        db_models.KnownTagsAnon
    ).values(
        counter=0
    )

    conn.execute(stmt)


def set_all_tag_counters_to_zero(
        conn: Connection,
        user: db_models.User,
) -> None:
    """Mark all counters as 0, so we could start recalculating."""
    stmt = sa.update(
        db_models.KnownTags
    ).where(
        db_models.KnownTags.user_uuid == user.uuid
    ).values(
        counter=0
    )

    conn.execute(stmt)


def rebuild_known_tags_for_anon_user(conn: Connection) -> tuple[int, int]:
    """Refresh known tags for anon user (without dropping)."""
    total_count = 0
    occurrences = 0

    public_users = get_public_users(conn)

    stmt = sa.select(
        db_models.Item.tags
    ).where(
        db_models.Item.owner_uuid.in_(tuple(public_users)),  # noqa
    )

    all_tags = conn.execute(stmt).fetchall()
    counters: dict[str, int] = defaultdict(int)

    for tag_group, in all_tags:
        occurrences += len(tag_group)
        for tag in tag_group:
            counters[str(tag).lower()] += 1
            total_count += 1

    for tag, counter in counters.items():
        insert = pg_insert(
            db_models.KnownTagsAnon
        ).values(
            tag=tag,
            counter=counter,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[
                db_models.KnownTagsAnon.tag,
            ],
            set_={'counter': insert.excluded.counter}
        )
        conn.execute(stmt)

    return total_count, occurrences


def rebuild_known_tags_for_known_user(
        conn: Connection,
        user: db_models.User,
) -> tuple[int, int]:
    """Refresh known tags for known user (without dropping)."""
    total_count = 0
    occurrences = 0

    stmt = sa.select(
        db_models.Item.tags
    ).where(
        sa.or_(
            db_models.Item.owner_uuid == user.uuid,
            db_models.Item.permissions.contains([str(user.uuid)]),
        )
    )

    all_tags = conn.execute(stmt).fetchall()
    counters: dict[str, int] = defaultdict(int)

    for tag_group, in all_tags:
        occurrences += len(tag_group)
        for tag in tag_group:
            counters[str(tag).lower()] += 1
            total_count += 1

    for tag, counter in counters.items():
        insert = pg_insert(
            db_models.KnownTags
        ).values(
            user_uuid=user.uuid,
            tag=tag,
            counter=counter,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[
                db_models.KnownTags.user_uuid,
                db_models.KnownTags.tag,
            ],
            set_={'counter': insert.excluded.counter}
        )
        conn.execute(stmt)

    return total_count, occurrences
