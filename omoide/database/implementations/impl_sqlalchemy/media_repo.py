"""Repository that perform CRUD operations on media."""

from datetime import datetime

import sqlalchemy as sa

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_media_repo import AbsMediaRepo

LOG = custom_logging.get_logger(__name__)


class MediaRepo(AbsMediaRepo):
    """Repository that perform CRUD operations on media."""

    async def create_media(self, media: models.Media) -> int:
        """Create Media, return media id."""
        stmt = (
            sa.insert(db_models.Media)
            .values(**media.model_dump(exclude={'id'}))
            .returning(db_models.Media.id)
        )

        media_id = await self.db.execute(stmt)
        return int(media_id)

    async def delete_processed_media(self, user: models.User) -> int:
        """Delete fully downloaded media rows."""
        stmt = sa.delete(db_models.Media).where(
            db_models.Media.processed_at != sa.null(),
            db_models.Media.error == sa.null(),
            db_models.Media.owner_uuid == user.uuid,
        )

        response = await self.db.execute(stmt)
        return int(response.rowcount)

    async def delete_all_processed_media(self) -> int:
        """Delete fully downloaded media rows."""
        stmt = sa.delete(db_models.Media).where(
            db_models.Media.processed_at != sa.null(),
            db_models.Media.error == sa.null(),
        )

        response = await self.db.execute(stmt)
        return int(response.rowcount)

    async def copy_image(
        self,
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
                owner_uuid=str(source_item.owner_uuid),
                source_uuid=str(source_item.uuid),
                target_uuid=str(target_item.uuid),
                media_type=media_type,
                ext=ext,
            )
            .returning(db_models.CommandCopy.id)
        )

        copy_id = await self.db.execute(stmt)
        return int(copy_id)

    async def mark_file_as_orphan(
        self,
        item: models.Item,
        media_type: const.MEDIA_TYPE,
        ext: str,
        moment: datetime,
    ) -> None:
        """Mark corresponding files as useless."""
        stmt = sa.insert(db_models.OrphanFiles).values(
            media_type=media_type,
            owner_uuid=item.owner_uuid,
            item_uuid=item.uuid,
            ext=ext,
            moment=moment,
        )
        await self.db.execute(stmt)
