"""Storage implementation."""

import sqlalchemy as sa

from omoide import custom_logging
from omoide import models
from omoide.database import db_models
from omoide.workers.common.database import PostgreSQLDatabase

LOG = custom_logging.get_logger(__name__)


class DownloaderPostgreSQLDatabase(PostgreSQLDatabase):
    """Storage in database."""

    def get_media_candidates(self, batch_size: int) -> list[int]:
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

    def load_media(self, target_id: int) -> models.OutputMedia:
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

    def delete_media(self, target_id: int) -> None:
        """Delete specific object."""
        stmt = sa.delete(db_models.QueueOutputMedia).where(
            db_models.QueueOutputMedia.id == target_id
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)
