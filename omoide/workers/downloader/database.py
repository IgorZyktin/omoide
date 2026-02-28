"""Storage implementation."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide.database import db_models
from omoide.workers.common.database import PostgreSQLDatabase

LOG = custom_logging.get_logger(__name__)


class DownloaderPostgreSQLDatabase(PostgreSQLDatabase):
    """Storage in database."""

    def get_output_media_candidates(self, batch_size: int) -> list[int]:
        """Return candidates to operate on."""
        query = (
            sa.select(db_models.QueueOutputMedia.id)
            .where(
                db_models.QueueOutputMedia.lock == sa.null(),
                db_models.QueueOutputMedia.error == sa.null(),
            )
            .order_by(db_models.QueueOutputMedia.id)
            .limit(batch_size)
        )

        with self.engine.begin() as conn:
            response = conn.execute(query).all()

        return [x for (x,) in response]

    def lock(self, target_id: int, name: str) -> bool:
        """Lock specific object."""
        stmt = (
            sa.update(db_models.QueueOutputMedia)
            .values(
                lock=name,
            )
            .where(
                db_models.QueueOutputMedia.id == target_id,
                db_models.QueueOutputMedia.lock == sa.null(),
            )
        )

        with self.engine.begin() as conn:
            response = conn.execute(stmt)

        return bool(response.rowcount)

    def get_output_media(self, target_id: int) -> models.OutputMedia:
        """Load data from storage."""
        query = sa.select(db_models.QueueOutputMedia).where(
            db_models.QueueOutputMedia.id == target_id
        )

        with self.engine.begin() as conn:
            response = conn.execute(query).one()

        return models.OutputMedia(
            id=response.id,
            user_uuid=response.user_uuid,
            item_uuid=response.item_uuid,
            created_at=response.created_at,
            ext=response.ext,
            content_type=response.content_type,
            media_type=response.media_type,
            extras=response.extras,
            error=response.error,
            content=response.content,
            processed_by=set(response.processed_by),
        )

    def mark_failed_and_release_lock(self, target_id: int, error: str) -> None:
        """Mark object as unprocessable."""
        stmt = (
            sa.update(db_models.QueueOutputMedia)
            .values(
                lock=None,
                error=error,
            )
            .where(db_models.QueueOutputMedia.id == target_id)
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def delete_output_media(self, target_id: int) -> None:
        """Delete specific object."""
        stmt = sa.delete(db_models.QueueOutputMedia).where(
            db_models.QueueOutputMedia.id == target_id
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def get_item_id(self, item_uuid: UUID) -> int:
        """Return id."""
        query = sa.select(db_models.Item.id).where(
            db_models.Item.uuid == item_uuid
        )

        with self.engine.begin() as conn:
            response = conn.execute(query).one()

            if response is None:
                msg = f'Item {item_uuid} does not exist'
                raise exceptions.DoesNotExistError(msg)

        return int(response.id)

    def update_metainfo(
        self,
        item_id: int,
        updated_at: datetime | None = None,
        content_width: int | None = None,
        content_height: int | None = None,
        content_size: int | None = None,
        preview_width: int | None = None,
        preview_height: int | None = None,
        preview_size: int | None = None,
        thumbnail_width: int | None = None,
        thumbnail_height: int | None = None,
        thumbnail_size: int | None = None,
    ) -> None:
        """Update item metainfo."""
        raw_values = {
            'updated_at': updated_at,
            'content_width': content_width,
            'content_height': content_height,
            'content_size': content_size,
            'preview_width': preview_width,
            'preview_height': preview_height,
            'preview_size': preview_size,
            'thumbnail_width': thumbnail_width,
            'thumbnail_height': thumbnail_height,
            'thumbnail_size': thumbnail_size,
        }
        stmt = (
            sa.update(db_models.Metainfo)
            .values(
                **{
                    key: value
                    for key, value in raw_values.items()
                    if value is not None
                }
            )
            .where(db_models.Metainfo.item_id == item_id)
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def save_cr32_signature(
        self,
        item_id: int,
        signature: int,
    ) -> None:
        """Create signature record."""
        insert = pg_insert(db_models.SignatureCRC32).values(
            item_id=item_id,
            signature=signature,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.SignatureCRC32.item_id],
            set_={'signature': insert.excluded.signature},
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def save_md5_signature(
        self,
        item_id: int,
        signature: str,
    ) -> None:
        """Create signature record."""
        insert = pg_insert(db_models.SignatureMD5).values(
            item_id=item_id,
            signature=signature,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.SignatureMD5.item_id],
            set_={'signature': insert.excluded.signature},
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def save_exif(self, item_id: int, exif: models.Exif) -> None:
        """Update existing EXIF for the given item or create new one."""
        insert = pg_insert(db_models.EXIF).values(
            item_id=item_id,
            exif=exif.exif,
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[db_models.EXIF.item_id],
            set_={'exif': insert.excluded.exif},
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def is_fully_downloaded(self, item_id: int, *, skip_content: bool) -> bool:
        """Return True if item is downloaded."""
        query = sa.select(db_models.Metainfo).where(
            db_models.Metainfo.item_id == item_id
        )
        with self.engine.begin() as conn:
            response = conn.execute(query).one()

        if skip_content:
            return (
                response.preview_size is not None
                and response.thumbnail_size is not None
            )

        return (
            response.content_size is not None
            and response.preview_size is not None
            and response.thumbnail_size is not None
        )

    def mark_available(self, item_id: int) -> None:
        """Mark item as available."""
        stmt = (
            sa.update(db_models.Item)
            .values(
                status=models.Status.AVAILABLE,
            )
            .where(db_models.Item.id == item_id)
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)
