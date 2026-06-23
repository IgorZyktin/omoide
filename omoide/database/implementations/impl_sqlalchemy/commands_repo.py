"""Repository that performs operations on commands."""

import python_utilz as pu
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_commands_repo import AbsCommandsRepo


class CommandsRepo(AbsCommandsRepo[AsyncConnection]):
    """Repository that performs operations on commands."""

    async def soft_delete(
        self,
        conn: AsyncConnection,
        requested_by: models.User,
        item: models.Item,
    ) -> int:
        """Soft delete an item."""
        now = pu.now()
        stmt = (
            sa.insert(db_models.ParallelCommand)
            .values(
                requested_by=requested_by.id,
                name=models.Command.SOFT_DELETE,
                status=models.CommandStatus.CREATED,
                extras={'item_id': item.id},
                log='',
                created_at=now,
                updated_at=now,
                started_at=None,
                ended_at=None,
            )
            .returning(db_models.ParallelCommand.id)
        )
        command_id = (await conn.execute(stmt)).scalar()
        return command_id if command_id is not None else -1

    async def hard_delete(
        self,
        conn: AsyncConnection,
        requested_by: models.User,
        item: models.Item,
    ) -> int:
        """Hard delete an item."""
        now = pu.now()
        stmt = (
            sa.insert(db_models.ParallelCommand)
            .values(
                requested_by=requested_by.id,
                name=models.Command.HARD_DELETE,
                status=models.CommandStatus.CREATED,
                extras={'item_id': item.id},
                log='',
                created_at=now,
                updated_at=now,
                started_at=None,
                ended_at=None,
            )
            .returning(db_models.ParallelCommand.id)
        )
        command_id = (await conn.execute(stmt)).scalar()
        return command_id if command_id is not None else -1
