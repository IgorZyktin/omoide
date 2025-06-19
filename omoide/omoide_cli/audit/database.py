"""Audit database wrapper."""

import python_utilz as pu
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import custom_logging
from omoide.database import db_models
from omoide.database.implementations.impl_sqlalchemy import SqlalchemyDatabase
from omoide.omoide_cli.common import Triplet

LOG = custom_logging.get_logger(__name__)


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

    @staticmethod
    async def get_items_without_metainfo(conn: AsyncConnection) -> list[Triplet]:
        """Return items without metainfo."""
        query = (
            sa.select(
                db_models.Item.id,
                db_models.Item.uuid,
                db_models.Item.name,
            )
            .outerjoin(
                db_models.Metainfo,
                db_models.Metainfo.item_id == db_models.Item.id,
            )
            .where(db_models.Metainfo.item_id.is_(None))
        )
        response = (await conn.execute(query)).all()
        return [Triplet(*row) for row in response]

    @staticmethod
    async def create_metainfo(conn: AsyncConnection, item: Triplet) -> None:
        """Create new metainfo the item."""
        now = pu.now()
        stmt = sa.insert(db_models.Metainfo).values(
            item_id=item.id,
            created_at=now,
            updated_at=now,
        )
        await conn.execute(stmt)

    @staticmethod
    async def get_items_without_images(conn: AsyncConnection) -> list[Triplet]:
        """Return items without images."""
        query = sa.select(
            db_models.Item.id,
            db_models.Item.uuid,
            db_models.Item.name,
        ).where(db_models.Item.content_ext.is_(None))
        response = (await conn.execute(query)).all()
        return [Triplet(*row) for row in response]
