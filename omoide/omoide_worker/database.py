"""Database helper class for Worker."""

import python_utilz as pu
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import const
from omoide import custom_logging
from omoide.database import db_models
from omoide.storage.database.sync_db import SyncDatabase

LOG = custom_logging.get_logger(__name__)


class WorkerDatabase(SyncDatabase):
    """Database helper class for Worker."""

    def get_copies_batch(
        self,
        batch_size: int,
        last_seen: int | None,
    ) -> list[db_models.CommandCopy]:
        """Return list of images to copy."""
        query = self.session.query(db_models.CommandCopy).filter(
            db_models.CommandCopy.processed_at == sa.null(),
            db_models.CommandCopy.error == sa.null(),
        )

        if last_seen is not None:
            query = query.filter(db_models.CommandCopy.id > last_seen)

        query = query.order_by(db_models.CommandCopy.id).limit(batch_size)

        return query.all()

    def get_media_batch(
        self,
        batch_size: int,
        last_seen: int | None,
    ) -> list[db_models.Media]:
        """Return list of media records to download."""
        query = self.session.query(db_models.Media).filter(
            db_models.Media.processed_at == sa.null(),
            db_models.Media.error == sa.null(),
        )

        if last_seen is not None:
            query = query.filter(db_models.Media.id > last_seen)

        query = query.order_by(db_models.Media.id).limit(batch_size)

        return query.all()

    @staticmethod
    def create_media_from_copy(
        command: db_models.CommandCopy,
        content: bytes,
    ) -> db_models.Media:
        """Convert copy operation into media."""
        return db_models.Media(
            owner_uuid=command.owner.uuid,
            item_uuid=command.target.uuid,
            media_type=command.media_type,
            created_at=pu.now(),
            processed_at=None,
            content=content,
            ext=command.ext,
        )

    def mark_origin(self, command: db_models.CommandCopy) -> None:
        """Mark where item got its image."""
        insert = pg_insert(db_models.ItemNote).values(
            item_id=command.source_id,
            key='copied_image_from',
            value=str(command.source.uuid),
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[
                db_models.ItemNote.item_id,
                db_models.ItemNote.key,
            ],
            set_={'value': insert.excluded.value},
        )
        self.session.execute(stmt)

    @staticmethod
    def copy_parameters(command: db_models.CommandCopy, size: int) -> None:
        """Copy width/height from origin."""
        if not command.source:
            msg = (
                f'Source item {command.source.uuid} does not exist, '
                f'cannot copy image for {command.id}'
            )
            raise RuntimeError(msg)

        if not command.target:
            msg = (
                f'Target item {command.target.uuid} does not exist, '
                f'cannot copy image for {command.id}'
            )
            raise RuntimeError(msg)

        if command.media_type == const.CONTENT:
            command.target.metainfo.content_size = size
            command.target.metainfo.content_width = command.source.metainfo.content_width
            command.target.metainfo.content_height = command.source.metainfo.content_height
            command.target.content_ext = command.source.content_ext
            command.target.metainfo.content_type = command.source.metainfo.content_type

        elif command.media_type == const.PREVIEW:
            command.target.metainfo.preview_size = size
            command.target.metainfo.preview_width = command.source.metainfo.preview_width
            command.target.metainfo.preview_height = command.source.metainfo.preview_height
            command.target.preview_ext = command.source.preview_ext

        elif command.media_type == const.THUMBNAIL:
            command.target.metainfo.thumbnail_size = size
            command.target.metainfo.thumbnail_width = command.source.metainfo.thumbnail_width
            command.target.metainfo.thumbnail_height = command.source.metainfo.thumbnail_height
            command.target.thumbnail_ext = command.source.thumbnail_ext

        else:
            msg = f'Got unknown media_type {command.media_type} for copy command {command.id}'
            raise ValueError(msg)

    def drop_media(self) -> int:
        """Delete fully downloaded media rows, return total amount."""
        stmt = sa.delete(db_models.Media).where(
            db_models.Media.processed_at != sa.null(),
            db_models.Media.error == sa.null(),
        )

        with self._engine.begin() as conn:
            response = conn.execute(stmt)

        return int(response.rowcount)

    def drop_copies(self) -> int:
        """Delete complete copy operations, return total deleted amount."""
        stmt = sa.delete(db_models.CommandCopy).where(
            db_models.CommandCopy.processed_at != sa.null(),
            db_models.CommandCopy.error == sa.null(),
        )

        with self._engine.begin() as conn:
            response = conn.execute(stmt)

        return int(response.rowcount)
