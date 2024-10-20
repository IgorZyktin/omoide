"""Repository that performs operations on tags."""

import abc
import itertools
from collections import defaultdict
from typing import Callable

import sqlalchemy as sa
from sqlalchemy import Connection

from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_tags_repo import AbsTagsRepo


class _TagsRepoHelper(AbsTagsRepo[Connection], abc.ABC):
    """Helper class."""

    @staticmethod
    def _process_batch_of_tags(
        conn: Connection,
        get_conditions: Callable[[int], list[sa.ColumnElement]],
        batch_size: int,
    ) -> dict[str, int]:
        """Process batch of tags load."""
        known_tags: dict[str, int] = defaultdict(int)
        marker = -1

        while True:
            stmt = (
                (
                    sa.select(
                        db_models.Item.id,
                        db_models.ComputedTags.tags,
                    )
                    .join(
                        db_models.ComputedTags,
                        db_models.ComputedTags.item_uuid
                        == db_models.Item.uuid,
                    )
                    .where(*get_conditions(marker))
                )
                .order_by(db_models.Item.id)
                .limit(batch_size)
            )

            response = conn.execute(stmt).fetchall()

            for item_id, item_tags in response:
                for item_tag in item_tags:
                    known_tags[item_tag.casefold()] += 1
                marker = item_id

            if len(response) < batch_size:
                break

        return dict(known_tags)


class TagsRepo(_TagsRepoHelper):
    """Repository that performs operations on tags."""

    def get_known_tags_anon(
        self,
        conn: Connection,
        batch_size: int,
    ) -> dict[str, int]:
        """Return known tags for anon."""
        public_users = sa.select(db_models.PublicUsers.user_uuid)

        def get_conditions(_marker: int) -> list[sa.ColumnElement]:
            """Return list of filtering conditions."""
            return [
                db_models.Item.owner_uuid.in_(public_users),
                db_models.Item.id > _marker,
            ]

        return self._process_batch_of_tags(
            conn=conn,
            get_conditions=get_conditions,
            batch_size=batch_size,
        )

    def drop_known_tags_anon(self, conn: Connection) -> int:
        """Drop all known tags for anon user."""
        stmt = sa.delete(db_models.KnownTagsAnon)
        response = conn.execute(stmt)
        return int(response.rowcount)

    def insert_known_tags_anon(
        self,
        conn: Connection,
        tags: dict[str, int],
        batch_size: int,
    ) -> None:
        """Insert given tags for anon user."""
        payload = [
            {'tag': str(tag), 'counter': counter}
            for tag, counter in tags.items()
        ]

        for batch in itertools.batched(payload, batch_size):
            stmt = sa.insert(db_models.KnownTagsAnon).values(batch)
            conn.execute(stmt)

    def get_known_tags_user(
        self,
        conn: Connection,
        user: models.User,
        batch_size: int,
    ) -> dict[str, int]:
        """Return known tags for specific user."""

        def get_conditions(_marker: int) -> list[sa.ColumnElement]:
            """Return list of filtering conditions."""
            return [
                sa.or_(
                    db_models.Item.owner_uuid == user.uuid,
                    db_models.Item.permissions.any(
                        str(user.uuid)  # type: ignore
                    ),
                ),
                db_models.Item.id > _marker,
            ]

        return self._process_batch_of_tags(
            conn=conn,
            get_conditions=get_conditions,
            batch_size=batch_size,
        )

    def drop_known_tags_user(
        self,
        conn: Connection,
        user: models.User,
    ) -> int:
        """Drop all known tags for specific user."""
        stmt = sa.delete(db_models.KnownTags).where(
            db_models.KnownTags.user_id == user.id
        )
        response = conn.execute(stmt)
        return int(response.rowcount)

    def insert_known_tags_user(
        self,
        conn: Connection,
        user: models.User,
        tags: dict[str, int],
        batch_size: int,
    ) -> None:
        """Insert given tags for specific user."""
        payload = [
            {'user_id': user.id, 'tag': str(tag), 'counter': counter}
            for tag, counter in tags.items()
        ]

        for batch in itertools.batched(payload, batch_size):
            stmt = sa.insert(db_models.KnownTags).values(batch)
            conn.execute(stmt)
