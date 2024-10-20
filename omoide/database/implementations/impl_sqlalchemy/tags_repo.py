"""Repository that performs operations on tags."""

import itertools
from collections import defaultdict

import sqlalchemy as sa
from sqlalchemy import Connection

from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_tags_repo import AbsTagsRepo


class TagsRepo(AbsTagsRepo[Connection]):
    """Repository that performs operations on tags."""

    def get_known_tags_anon(
        self,
        conn: Connection,
        batch_size: int,
    ) -> dict[str, int]:
        """Return known tags for anon."""
        known_tags: dict[str, int] = defaultdict(int)
        public_users = sa.select(db_models.PublicUsers.user_uuid)
        marker = -1

        while True:
            stmt = (
                sa.select(
                    db_models.Item.id,
                    db_models.ComputedTags.tags,
                )
                .join(
                    db_models.ComputedTags,
                    db_models.ComputedTags.item_uuid == db_models.Item.uuid,
                )
                .where(
                    db_models.Item.owner_uuid.in_(public_users),
                    db_models.Item.id > marker,
                )
            ).order_by(db_models.Item.id).limit(batch_size)

            response = conn.execute(stmt).fetchall()

            for item_id, item_tags in response:
                for item_tag in item_tags:
                    known_tags[item_tag.casefold()] += 1
                marker = item_id

            if len(response) < batch_size:
                break

        return dict(known_tags)

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
        known_tags: dict[str, int] = defaultdict(int)
        public_users = sa.select(db_models.PublicUsers.user_uuid)
        marker = -1

        while True:
            stmt = (
                sa.select(
                    db_models.Item.id,
                    db_models.ComputedTags.tags,
                )
                .join(
                    db_models.ComputedTags,
                    db_models.ComputedTags.item_uuid == db_models.Item.uuid,
                )
                .where(
                    sa.or_(
                        db_models.Item.owner_uuid.in_(public_users),
                        db_models.Item.permissions.any(
                            str(user.uuid)  # type: ignore
                        ),
                    ),
                    db_models.Item.id > marker,
                )
            ).order_by(db_models.Item.id).limit(batch_size)

            response = conn.execute(stmt).fetchall()

            for item_id, item_tags in response:
                for item_tag in item_tags:
                    known_tags[item_tag.casefold()] += 1
                marker = item_id

            if len(response) < batch_size:
                break

        return dict(known_tags)

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
