"""Repository that perform CRUD operations on media.
"""
from uuid import UUID

import sqlalchemy as sa

from omoide import utils
from omoide.domain import errors
from omoide.domain.core import core_models
from omoide.domain.storage.interfaces.in_rp_media import AbsMediaRepository
from omoide.infra import custom_logging
from omoide.storage.database import db_models

LOG = custom_logging.get_logger(__name__)


class MediaRepository(AbsMediaRepository):
    """Repository that perform CRUD operations on media."""

    async def create_media(
            self,
            media: core_models.Media,
    ) -> core_models.Media:
        """Create Media."""
        stmt = sa.insert(
            db_models.Media
        ).values(
            created_at=media.created_at,
            processed_at=media.processed_at,
            error=None,
            owner_uuid=media.owner_uuid,
            item_uuid=media.item_uuid,
            media_type=media.media_type,
            content=media.content,
            ext=media.ext,
        ).returning(db_models.Media.id)

        media_id = await self.db.execute(stmt)
        media.id = media_id

        return media

    async def copy_media(
            self,
            owner_uuid: UUID,
            source_uuid: UUID,
            target_uuid: UUID,
            media_type: str,
            ext: str,
    ) -> int | errors.Error:
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

        result: int | errors.Error  # -----------------------------------------

        try:
            copy_id = await self.db.execute(stmt)
        except Exception as exc:
            LOG.exception('Failed to create manual copy')  # TODO - refactor
            result = errors.DatabaseError(exception=exc)
        else:
            result = copy_id

        return result
