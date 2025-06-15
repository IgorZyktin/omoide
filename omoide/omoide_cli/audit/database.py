"""Audit database wrapper."""

from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import custom_logging
from omoide.database import db_models
from omoide.database.implementations.impl_sqlalchemy import SqlalchemyDatabase

LOG = custom_logging.get_logger(__name__)


@dataclass(frozen=True, eq=True)
class Triplet:
    """DTO for users and items."""

    id: int
    uuid: UUID
    name: str


class AuditDatabase(SqlalchemyDatabase):
    """Audit database wrapper."""

    @staticmethod
    async def get_users_to_root_items(conn: AsyncConnection) -> list[tuple[Triplet, Triplet]]:
        """Return users to root items join."""
        query = (
            sa.select(
                db_models.User.id,
                db_models.User.uuid,
                db_models.User.name,
                db_models.Item.id,
                db_models.Item.uuid,
                db_models.Item.name,
            )
            .outerjoin(
                db_models.Item,
                db_models.Item.owner_id == db_models.User.id,
            )
            .where(db_models.Item.parent_id.is_(None))
        )
        response = (await conn.execute(query)).all()
        return [(Triplet(x[0], x[1], x[2]), Triplet(x[3], x[4], x[5])) for x in response]

    @staticmethod
    async def fix_root_item(conn: AsyncConnection, user: Triplet) -> None:
        """Create new root item for the user."""
        _ = conn
        # TODO
        LOG.warning(
            'Expected to create new root item for user {user}), '
            'but this logic is not yet implemented',
            user=user,
        )
