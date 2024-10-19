"""Rebuild known tags for users."""

import abc
from collections import defaultdict
from collections.abc import Awaitable
from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import custom_logging
from omoide.domain import SerialOperation
from omoide.storage.database import db_models

if TYPE_CHECKING:
    from omoide.database.implementations.impl_sqlalchemy.database import (
        SqlalchemyDatabase,
    )

LOG = custom_logging.get_logger(__name__)


class BaseRebuildKnownTagsOperation(SerialOperation, abc.ABC):
    """Base class for known tags operations."""

    @staticmethod
    async def _get_tags_batched(
        func: Callable[..., Awaitable[list[tuple[int, list[str]]]]],
        conn: AsyncConnection,
        batch_size: int,
        *args: Any,
    ) -> dict[str, int]:
        """Process items in batches."""
        marker: int | None = None
        known_tags: dict[str, int] = defaultdict(int)

        while True:
            batch = await func(conn, marker, batch_size, *args)

            for item_id, tags in batch:
                for tag in tags:
                    known_tags[tag.casefold()] += 1

                marker = item_id

            if len(batch) < batch_size or marker is None:
                break

        return dict(known_tags)


class RebuildKnownTagsAnon(BaseRebuildKnownTagsOperation):
    """Rebuild known tags for anon."""

    name: str = 'rebuild_known_tags_anon'

    def __str__(self) -> str:
        """Return textual representation."""
        return f'<{self.id}, {self.name!r}>'

    @staticmethod
    async def _get_available_tags_anon(
        conn: AsyncConnection,
        marker: int | None,
        limit: int,
    ) -> list[tuple[int, list[str]]]:
        """Return known tags for anon."""
        sub_query = sa.select(db_models.PublicUsers.user_uuid)

        stmt = (
            sa.select(
                db_models.Item.id,
                db_models.Item.uuid,
                db_models.ComputedTags.tags,
            )
            .join(
                db_models.ComputedTags,
                db_models.ComputedTags.item_uuid == db_models.Item.uuid,
            )
            .where(
                db_models.Item.owner_uuid.in_(sub_query),
            )
        )

        if marker is not None:
            stmt = stmt.where(db_models.Item.id > marker)

        stmt = stmt.order_by(db_models.Item.id).limit(limit)

        response = (await conn.execute(stmt)).fetchall()
        return [(row.id, row.tags) for row in response]

    @staticmethod
    async def _drop_known_tags_anon(conn: AsyncConnection) -> None:
        """Drop all known tags for anon user."""
        stmt = sa.delete(db_models.KnownTagsAnon)
        await conn.execute(stmt)

    @staticmethod
    async def _insert_known_tags_anon(
        conn: AsyncConnection,
        tags: dict[str, int],
    ) -> None:
        """Drop all known tags for anon user."""
        for tag, counter in tags.items():
            stmt = sa.insert(db_models.KnownTagsAnon).values(
                tag=tag,
                counter=counter,
            )
            await conn.execute(stmt)

    async def execute(self, **kwargs: Any) -> bool:
        """Perform workload."""
        database: SqlalchemyDatabase = kwargs['database']
        batch_size: int = kwargs['batch_size']

        async with database.transaction() as conn:
            tags = await self._get_tags_batched(
                self._get_available_tags_anon, conn, batch_size
            )
            await self._drop_known_tags_anon(conn)
            await self._insert_known_tags_anon(conn, tags)

        return bool(tags)


class RebuildKnownTagsKnow(BaseRebuildKnownTagsOperation):
    """Rebuild known tags for specific user."""

    name: str = 'rebuild_known_tags_known'

    def __str__(self) -> str:
        """Return textual representation."""
        user_uuid = self.extras['user_uuid']
        return f'<{self.id}, {self.name!r} for user {user_uuid}>'

    @staticmethod
    async def _get_available_tags_known(
        conn: AsyncConnection,
        marker: int | None,
        limit: int,
        user_id: int,
    ) -> list[tuple[int, list[str]]]:
        """Return known tags for known user."""
        subquery = (
            sa.select(db_models.User.uuid)
            .where(db_models.User.id == user_id)
            .subquery('uuid_conversion')
        )

        stmt = (
            sa.select(
                db_models.Item.id,
                db_models.Item.uuid,
                db_models.ComputedTags.tags,
                db_models.Item.permissions,
            )
            .join(
                db_models.ComputedTags,
                db_models.ComputedTags.item_uuid == db_models.Item.uuid,
            )
            .where(
                sa.or_(
                    db_models.Item.owner_uuid == subquery,
                    db_models.Item.permissions.any(subquery),
                )
            )
        )

        if marker is not None:
            stmt = stmt.where(db_models.Item.id > marker)

        stmt = stmt.order_by(db_models.Item.id).limit(limit)

        response = (await conn.execute(stmt)).fetchall()
        return [(row.id, row.tags) for row in response]

    @staticmethod
    async def _drop_known_tags_known(
        conn: AsyncConnection,
        user_id: int,
    ) -> None:
        """Drop all known tags for known user."""
        stmt = sa.delete(db_models.KnownTags).where(
            db_models.KnownTags.user_id == user_id
        )
        await conn.execute(stmt)

    @staticmethod
    async def _insert_known_tags_known(
        conn: AsyncConnection,
        user_id: int,
        tags: dict[str, int],
    ) -> None:
        """Drop all known tags for known user."""
        payload = [
            {'user_id': user_id, 'tag': tag, 'counter': counter}
            for tag, counter in tags.items()
        ]
        stmt = sa.insert(db_models.KnownTags).values(payload)
        await conn.execute(stmt)

    async def execute(self, **kwargs: Any) -> bool:
        """Perform workload."""
        database: SqlalchemyDatabase = kwargs['database']
        batch_size: int = kwargs['batch_size']
        user_id: id = self.extras['user_id']

        async with database.transaction() as conn:
            tags = await self._get_tags_batched(
                self._get_available_tags_known, conn, batch_size, user_id
            )
            await self._drop_known_tags_known(conn, user_id)
            await self._insert_known_tags_known(conn, user_id, tags)

        return bool(tags)
