"""Repository that perform CRUD operations on media."""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_media_repo import AbsMediaRepo

LOG = custom_logging.get_logger(__name__)


class MediaRepo(AbsMediaRepo[AsyncConnection]):
    """Repository that perform CRUD operations on media."""

    async def create_media(self, conn: AsyncConnection, media: models.Media) -> int:
        """Create Media, return media id."""
        stmt = (
            sa.insert(db_models.Media)
            .values(**media.model_dump(exclude={'id'}))
            .returning(db_models.Media.id)
        )

        media_id = (await conn.execute(stmt)).scalar()
        return media_id if media_id is not None else -1

    async def delete_processed_media(self, conn: AsyncConnection, user: models.User) -> int:
        """Delete fully downloaded media rows."""
        stmt = sa.delete(db_models.Media).where(
            db_models.Media.processed_at != sa.null(),
            db_models.Media.error == sa.null(),
            db_models.Media.owner_id == user.id,
        )

        response = await conn.execute(stmt)
        return int(response.rowcount)

    async def delete_all_processed_media(self, conn: AsyncConnection) -> int:
        """Delete fully downloaded media rows."""
        stmt = sa.delete(db_models.Media).where(
            db_models.Media.processed_at != sa.null(),
            db_models.Media.error == sa.null(),
        )

        response = await conn.execute(stmt)
        return int(response.rowcount)

    async def copy_image(
        self,
        conn: AsyncConnection,
        source_item: models.Item,
        target_item: models.Item,
        media_type: const.MEDIA_TYPE,
        ext: str,
        moment: datetime,
    ) -> int:
        """Save intention to copy data between items."""
        stmt = (
            sa.insert(db_models.CommandCopy)
            .values(
                created_at=moment,
                processed_at=None,
                error=None,
                owner_id=str(source_item.owner_id),
                source_id=str(source_item.id),
                target_id=str(target_item.id),
                media_type=media_type,
                ext=ext,
            )
            .returning(db_models.CommandCopy.id)
        )

        copy_id = (await conn.execute(stmt)).scalar()
        return int(copy_id) if copy_id is not None else -1
