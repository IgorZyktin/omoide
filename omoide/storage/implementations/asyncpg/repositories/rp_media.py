"""Repository that perform CRUD operations on media."""
from uuid import UUID

import sqlalchemy as sa

from omoide import models
from omoide import utils
from omoide.infra import custom_logging
from omoide.storage import interfaces
from omoide.storage.database import db_models
from omoide.storage.implementations import asyncpg

LOG = custom_logging.get_logger(__name__)


class MediaRepository(interfaces.AbsMediaRepository, asyncpg.AsyncpgStorage):
    """Repository that perform CRUD operations on media."""

    async def create_media(self, media: models.Media) -> int:
        """Create Media, return media id."""
        stmt = sa.insert(
            db_models.Media
        ).values(
            **media.model_dump()
        ).returning(db_models.Media.id)

        media_id = await self.db.execute(stmt)
        return media_id

    async def delete_processed_media(self, user: models.User) -> int:
        """Delete fully downloaded media rows."""
        stmt = sa.delete(db_models.Media).where(
            db_models.Media.processed_at != None,  # noqa: E711
            db_models.Media.error == None,  # noqa: E711
            db_models.Media.owner_uuid == user.uuid,
        )

        response = await self.db.execute(stmt)
        return response.rowcount

    async def delete_all_processed_media(self) -> int:
        """Delete fully downloaded media rows."""
        stmt = sa.delete(db_models.Media).where(
            db_models.Media.processed_at != None,  # noqa: E711
            db_models.Media.error == None,  # noqa: E711
        )

        response = await self.db.execute(stmt)
        return response.rowcount

    async def copy_image(
        self,
        owner_uuid: UUID,
        source_uuid: UUID,
        target_uuid: UUID,
        media_type: str,
        ext: str,
    ) -> int:
        """Save intention to copy data between items."""
        stmt = sa.insert(
            db_models.CommandCopy
        ).values(
            created_at=utils.now(),
            processed_at=None,
            error=None,
            owner_uuid=str(owner_uuid),
            source_uuid=str(source_uuid),
            target_uuid=str(target_uuid),
            media_type=media_type,
            ext=ext,
        ).returning(db_models.CommandCopy.id)

        copy_id = await self.db.execute(stmt)
        return copy_id
