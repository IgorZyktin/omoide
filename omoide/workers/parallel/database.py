"""Storage implementation."""

from collections.abc import Collection

import python_utilz as pu
import sqlalchemy as sa

from omoide import custom_logging
from omoide import models
from omoide.database import db_models
from omoide.database.implementations.impl_sqlalchemy import SqlalchemyDatabase

LOG = custom_logging.get_logger(__name__)


class ParallelPostgreSQLDatabase(SqlalchemyDatabase):
    """Storage in database."""

    async def get_parallel_commands(
        self,
        batch_size: int,
        supported_operations: Collection[str],
    ) -> list[models.ParallelCommand]:
        """Return candidates to operate on."""
        query = (
            sa.select(db_models.ParallelCommand)
            .with_for_update(skip_locked=True)
            .where(
                db_models.ParallelCommand.status
                == models.CommandStatus.CREATED,
            )
        )

        if supported_operations:
            query = query.where(
                db_models.ParallelCommand.name.in_(tuple(supported_operations))
            )

        query = query.order_by(db_models.ParallelCommand.id).limit(batch_size)

        async with self._engine.begin() as conn:
            response = (await conn.execute(query)).fetchall()

        return [
            models.ParallelCommand(
                id=each.id,
                requested_by=each.requested_by,
                name=each.name,
                status=models.CommandStatus(each.status),
                extras=each.extras,
                log=each.log,
                created_at=each.created_at,
                updated_at=each.updated_at,
                started_at=each.started_at,
                ended_at=each.ended_at,
            )
            for each in response
        ]

    async def start_task(self, task: models.ParallelCommand) -> bool:
        """Start executing task."""
        now = pu.now()
        stmt = (
            sa.update(db_models.ParallelCommand)
            .values(
                started_at=now,
                updated_at=now,
                status=models.CommandStatus.ACTIVE,
            )
            .where(
                db_models.ParallelCommand.id == task.id,
                db_models.ParallelCommand.status
                == models.CommandStatus.CREATED,
            )
        )

        async with self._engine.begin() as conn:
            response = await conn.execute(stmt)

        return bool(response.rowcount)

    async def mark_done(self, task: models.ParallelCommand) -> None:
        """Mark object as unprocessable."""
        now = pu.now()
        stmt = (
            sa.update(db_models.ParallelCommand)
            .values(
                status=models.CommandStatus.DONE,
                updated_at=now,
                ended_at=now,
            )
            .where(db_models.ParallelCommand.id == task.id)
        )

        async with self._engine.begin() as conn:
            await conn.execute(stmt)

    async def mark_failed(
        self,
        task: models.ParallelCommand,
        error: str,
    ) -> None:
        """Mark object as unprocessable."""
        now = pu.now()
        stmt = (
            sa.update(db_models.ParallelCommand)
            .values(
                status=models.CommandStatus.FAILED,
                log=error,
                updated_at=now,
                ended_at=now,
            )
            .where(db_models.ParallelCommand.id == task.id)
        )

        async with self._engine.begin() as conn:
            await conn.execute(stmt)

    async def is_oid_referenced_elsewhere(
        self, oid: int, exclude_id: int
    ) -> bool:
        """Return True if any other command row still references this OID."""
        query = sa.select(
            sa.exists().where(
                db_models.ParallelCommand.id != exclude_id,
                db_models.ParallelCommand.extras['oid'].astext == str(oid),
            )
        )

        async with self._engine.begin() as conn:
            result = await conn.execute(query)
        return bool(result.scalar())
