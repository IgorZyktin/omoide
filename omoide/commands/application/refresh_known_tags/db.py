# -*- coding: utf-8 -*-
"""Database helpers.
"""
from typing import Iterator
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection

from omoide import utils
from omoide.commands.common.base_db import BaseDatabase
from omoide.storage.database import models


def get_users(database: BaseDatabase) -> list[models.User]:
    """Get all registered users."""
    with database.start_session() as session:
        return session.query(models.User).order_by(models.User.name).all()


def get_user(database: BaseDatabase, uuid: UUID) -> models.User:
    """Get specific registered users."""
    with database.start_session() as session:
        return session.query(models.User).get(str(uuid))


# Functions for known users ---------------------------------------------------


def refresh_known_tags_for_known_user(
        database: BaseDatabase,
        user: models.User,
) -> tuple[int, int, set[str]]:
    """Refresh known tags for known user (without dropping)."""
    total_count = 0
    actual_tags: set[str] = set()
    to_drop: set[str] = set()

    with database.engine.begin() as conn:
        cached_tags = get_all_cached_tags_for_known_user(conn, user)
        for tag in get_all_tags_for_known_user(conn, user):
            actual_tags.add(tag)
            counter = count_presence_for_known_user(conn, user, tag)
            total_count += counter

            if counter == 0:
                to_drop.add(tag)
            else:
                refresh_tag_counter_for_known_user(conn, user, tag, counter)

    to_drop.update(cached_tags - actual_tags)

    return len(actual_tags), total_count, to_drop


def get_all_cached_tags_for_known_user(
        conn: Connection,
        user: models.User,
) -> set[str]:
    """Get all unique tags from known tags table."""
    stmt = sa.select(
        sa.distinct(models.KnownTags.tag)
    ).where(
        models.KnownTags.user_uuid == user.uuid
    )
    response = conn.execute(stmt).fetchall()
    return {x for x, in response}


def get_all_tags_for_known_user(
        conn: Connection,
        user: models.User,
) -> Iterator[str]:
    """Get all unique tags for known user (but not UUIDs)."""
    subquery = sa.select(
        models.Item.uuid
    ).where(
        sa.or_(
            models.Item.owner_uuid == user.uuid,
            models.Item.permissions.any(str(user.uuid)),
        )
    )

    stmt = sa.select(
        sa.distinct(sa.func.unnest(models.ComputedTags.tags))
    ).where(
        models.ComputedTags.item_uuid.in_(subquery)  # noqa
    )

    for tag, in conn.execute(stmt):
        if not utils.is_valid_uuid(tag):
            yield tag


def count_presence_for_known_user(
        conn: Connection,
        user: models.User,
        tag: str,
) -> int:
    """Cont how many times this tag is used."""
    subquery = sa.select(
        models.Item.uuid
    ).where(
        sa.or_(
            models.Item.owner_uuid == user.uuid,
            models.Item.permissions.any(str(user.uuid))
        )
    )

    stmt = sa.select(
        sa.func.count()
    ).where(
        models.ComputedTags.item_uuid.in_(subquery),  # noqa
        models.ComputedTags.tags.any(tag),
    )

    counter = conn.execute(stmt).scalar()

    return int(counter or 0)


def refresh_tag_counter_for_known_user(
        conn: Connection,
        user: models.User,
        tag: str,
        counter: int,
) -> None:
    """Save new counter value."""
    insert = pg_insert(
        models.KnownTags
    ).values(
        user_uuid=user.uuid,
        tag=tag,
        counter=counter
    )

    stmt = insert.on_conflict_do_update(
        index_elements=[models.KnownTags.user_uuid, models.KnownTags.tag],
        set_={'counter': insert.excluded.counter}
    )
    conn.execute(stmt)


def drop_known_tags_for_known_user(
        database: BaseDatabase,
        user: models.User,
        tags: set[str],
) -> int:
    """Drop given list of tags for user."""
    with database.engine.begin() as conn:
        stmt = sa.delete(
            models.KnownTags
        ).where(
            models.KnownTags.user_uuid == user.uuid,
            models.KnownTags.tag.in_(tuple(tags))  # noqa
        )
        response = conn.execute(stmt)
        return int(response.rowcount)


# Functions for anon user -----------------------------------------------------


def refresh_known_tags_for_anon_user(
        database: BaseDatabase,
) -> tuple[int, int, set[str]]:
    """Refresh known tags for anon user (without dropping)."""
    total_count = 0
    actual_tags: set[str] = set()
    to_drop: set[str] = set()

    with database.engine.begin() as conn:
        cached_tags = get_all_cached_tags_for_anon_user(conn)
        for tag in get_all_tags_for_anon_user(conn):
            actual_tags.add(tag)
            counter = count_presence_for_anon_user(conn, tag)
            total_count += counter

            if counter == 0:
                to_drop.add(tag)
            else:
                refresh_tag_counter_for_anon_user(conn, tag, counter)

    to_drop.update(cached_tags - actual_tags)

    return len(actual_tags), total_count, to_drop


def get_all_cached_tags_for_anon_user(
        conn: Connection,
) -> set[str]:
    """Get all unique tags for anon user (but not UUIDs)."""
    stmt = sa.select(
        sa.distinct(models.KnownTagsAnon.tag)
    )
    response = conn.execute(stmt).fetchall()
    return {x for x, in response}


def get_all_tags_for_anon_user(
        conn: Connection,
) -> Iterator[str]:
    """Get all unique tags for anon user (but not UUIDs)."""
    subquery = sa.select(
        models.Item.uuid
    ).where(
        models.Item.owner_uuid.in_(  # noqa
            sa.select(models.PublicUsers.user_uuid)
        )
    )

    stmt = sa.select(
        sa.distinct(sa.func.unnest(models.ComputedTags.tags))
    ).where(
        models.ComputedTags.item_uuid.in_(subquery)  # noqa
    )

    for tag, in conn.execute(stmt):
        if not utils.is_valid_uuid(tag):
            yield tag


def count_presence_for_anon_user(
        conn: Connection,
        tag: str,
) -> int:
    """Cont how many times this tag is used."""
    subquery = sa.select(
        models.Item.uuid
    ).where(
        models.Item.owner_uuid.in_(  # noqa
            sa.select(models.PublicUsers.user_uuid)
        )
    )

    stmt = sa.select(
        sa.func.count()
    ).where(
        models.ComputedTags.item_uuid.in_(subquery),  # noqa
        models.ComputedTags.tags.any(tag),
    )

    counter = conn.execute(stmt).scalar()

    return int(counter or 0)


def refresh_tag_counter_for_anon_user(
        conn: Connection,
        tag: str,
        counter: int,
) -> None:
    """Save new counter value."""
    insert = pg_insert(
        models.KnownTagsAnon
    ).values(
        tag=tag,
        counter=counter
    )

    stmt = insert.on_conflict_do_update(
        index_elements=[models.KnownTags.tag],
        set_={'counter': insert.excluded.counter}
    )
    conn.execute(stmt)


def drop_known_tags_for_anon_user(
        database: BaseDatabase,
        tags: set[str],
) -> int:
    """Drop given list of tags for anon user."""
    with database.engine.begin() as conn:
        stmt = sa.delete(
            models.KnownTagsAnon
        ).where(
            models.KnownTagsAnon.tag.in_(tuple(tags))  # noqa
        )
        response = conn.execute(stmt)
        return int(response.rowcount)
