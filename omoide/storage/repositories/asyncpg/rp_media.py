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
    ) -> core_models.Media | errors.Error:
        """Create Media."""
        stmt = sa.insert(
            db_models.Media
        ).values(
            created_at=media.created_at,
            processed_at=media.processed_at,
            error='',
            owner_uuid=media.owner_uuid,
            item_uuid=media.item_uuid,
            media_type=media.media_type,
            content=media.content,
            ext=media.ext,
        ).returning(db_models.Media.id)

        result: core_models.Media | errors.Error  # ---------------------------

        try:
            media_id = await self.db.execute(stmt)
        except Exception as exc:
            LOG.exception('Failed to create media')  # TODO - refactor
            result = errors.DatabaseError(exception=exc)
        else:
            media.id = media_id
            result = media

        return result

    async def get_media_by_id(
            self,
            media_id: int,
    ) -> core_models.Media | errors.Error:
        """Return Media."""
        stmt = sa.select(
            db_models.Media
        ).where(
            db_models.Media.id == media_id,
        )

        result: core_models.Media | errors.Error  # ---------------------------

        try:
            response = await self.db.fetch_one(stmt)
        except Exception as exc:
            LOG.exception('Failed to get media')  # TODO - refactor
            result = errors.DatabaseError(exception=exc)
        else:
            if response is None:
                result = errors.MediaDoesNotExist(media_id=media_id)
            else:
                result = core_models.Media(**response)

        return result

    async def delete_media(
            self,
            media_id: int,
    ) -> None | errors.Error:
        """Delete Media."""
        stmt = sa.delete(
            db_models.Media
        ).where(
            db_models.Media.id == media_id,
        ).returning(1)

        result: None | errors.Error  # ----------------------------------------

        try:
            response = await self.db.fetch_one(stmt)
        except Exception as exc:
            LOG.exception('Failed to delete media')  # TODO - refactor
            result = errors.DatabaseError(exception=exc)
        else:
            if response is None:
                result = errors.MediaDoesNotExist(media_id=media_id)
            else:
                result = None

        return result

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
            error='',
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
