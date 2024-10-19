"""Rebuild known tags for users."""

import abc
from collections import defaultdict
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import const
from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.database import db_models
from omoide.workers.serial.worker import SerialWorker

LOG = custom_logging.get_logger(__name__)


class BaseRebuildKnownTagsOperation(models.SerialOperation, abc.ABC):
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


@dataclass
class RebuildKnownTagsAnon(BaseRebuildKnownTagsOperation):
    """Rebuild known tags for anon."""

    name: str = const.SERIAL_REBUILD_KNOWN_TAGS_ANON

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
        LOG.info('Updating known tags for anon, operation_id={}', self.id)
        worker: SerialWorker = kwargs['worker']

        async with worker.database.transaction() as conn:
            tags = await self._get_tags_batched(
                self._get_available_tags_anon,
                conn,
                worker.config.batch_size,
            )
            await self._drop_known_tags_anon(conn)
            await self._insert_known_tags_anon(conn, tags)

        return True


@dataclass
class RebuildKnownTagsUser(BaseRebuildKnownTagsOperation):
    """Rebuild known tags for specific user."""

    name: str = const.SERIAL_REBUILD_KNOWN_TAGS_USER

    @staticmethod
    async def _get_available_tags_known(
        conn: AsyncConnection,
        marker: int | None,
        limit: int,
        user: models.User,
    ) -> list[tuple[int, list[str]]]:
        """Return known tags for known user."""
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
                    db_models.Item.owner_uuid == user.uuid,
                    db_models.Item.permissions.any(str(user.uuid)),
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
        user: models.User,
    ) -> None:
        """Drop all known tags for known user."""
        stmt = sa.delete(db_models.KnownTags).where(
            db_models.KnownTags.user_id == user.id
        )
        await conn.execute(stmt)

    @staticmethod
    async def _insert_known_tags_known(
        conn: AsyncConnection,
        user: models.User,
        tags: dict[str, int],
        batch_size: int,
    ) -> None:
        """Drop all known tags for known user."""
        payload = [
            {'user_id': user.id, 'tag': str(tag), 'counter': counter}
            for tag, counter in tags.items()
        ]

        for section in utils.group_to_size(payload, batch_size, default=None):
            clean_section = [x for x in section if x is not None]
            stmt = sa.insert(db_models.KnownTags).values(clean_section)
            await conn.execute(stmt)

    async def execute(self, **kwargs: Any) -> bool:
        """Perform workload."""
        worker = kwargs['worker']
        user_id: int = self.extras.get('user_id')
        user_uuid: str = self.extras.get('user_uuid')

        async with worker.database.transaction() as conn:
            users = await worker.users.select(
                conn,
                user_id=user_id,
                uuid=user_uuid,
                limit=1,
            )

            if users:
                LOG.info(
                    'Updating known tags for user {}, operation_id={}',
                    users[0],
                    self.id,
                )
            else:
                problem = (
                    f'User with uuid={user_uuid!r} '
                    f'or id={user_id!r} does not exist'
                )
                raise exceptions.BadSerialOperationError(problem=problem)

            user = users[0]
            batch_size: int = worker.config.batch_size
            tags = await self._get_tags_batched(
                self._get_available_tags_known, conn, batch_size, user
            )

            await self._drop_known_tags_known(conn, user)
            await self._insert_known_tags_known(conn, user, tags, batch_size)

        return True


class RebuildKnownTagsAll(RebuildKnownTagsUser):
    """Rebuild known tags for all registered users."""

    name: str = const.SERIAL_REBUILD_KNOWN_TAGS_ALL

    def __str__(self) -> str:
        """Return textual representation."""
        return f'<{self.id}, {self.name!r}>'

    async def execute(self, **kwargs: Any) -> bool:
        """Perform workload."""
        worker = kwargs['worker']
        batch_size = worker.config.batch_size

        async with worker.database.transaction() as conn:
            users = await worker.users.select(conn)

            for step, user in enumerate(users, start=1):
                LOG.info(
                    'Updating known tags for user {}, '
                    'operation_id={}, step {}',
                    user,
                    self.id,
                    step,
                )
                tags = await self._get_tags_batched(
                    self._get_available_tags_known,
                    conn, batch_size, user
                )
                await self._drop_known_tags_known(conn, user)
                await self._insert_known_tags_known(conn, user, tags,
                                                    batch_size)
        return True
