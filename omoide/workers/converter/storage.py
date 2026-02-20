"""Storage implementations."""

import sqlalchemy as sa

from omoide import models
from omoide.database import db_models
from omoide.workers.converter.interfaces import AbsStorage


class PostgreSQLStorage(AbsStorage):
    """Storage in database."""

    def __init__(self, url: str, *, echo: bool) -> None:
        """Initialize instance."""
        self.url = url
        self.echo = echo
        self.engine = sa.create_engine(url, pool_pre_ping=True, future=True)

    def get_candidates(self, batch_size: int) -> list[int]:
        """Return candidates to operate on."""
        query = sa.select(db_models.QueueInputMedia.id).where(
            db_models.QueueInputMedia.lock == sa.null(),
            db_models.QueueInputMedia.error == sa.null(),
        ).order_by(
            db_models.QueueInputMedia.id
        ).limit(batch_size)

        with self.engine.begin() as conn:
            response = conn.execute(query).all()

        return [x for x, in response]

    def lock(self, target_id: int, name: str) -> bool:
        """Lock specific object."""
        stmt = sa.update(db_models.QueueInputMedia).values(
            lock=name,
        ).where(
            db_models.QueueInputMedia.id == target_id
        )

        with self.engine.begin() as conn:
            response = conn.execute(stmt)

        return bool(response.rowcount)

    def load_model(self, target_id: int) -> models.InputMedia:
        """Load data from storage."""
        query = sa.select(db_models.QueueInputMedia).where(
            db_models.QueueInputMedia.id == target_id
        )

        with self.engine.begin() as conn:
            response = conn.execute(query).one()

        return models.InputMedia(
            id=response.id,
            item_id=response.item_id,
            created_at=response.created_at,
            filename=response.filename,
            content_type=response.content_type,
            extras=response.extras,
            error=response.error,
            content=response.content,
        )

    def save_model(self, model: models.InputMedia, media_type: str) -> None:
        """Save data to storage."""
        stmt = sa.insert(db_models.QueueOutputMedia).values(
            id=model.id,
            item_id=model.item_id,
            created_at=model.created_at,
            filename=model.filename,
            content_type=model.content_type,
            media_type=media_type,
            extras=model.extras,
            error=model.error,
            content=model.content,
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def mark_failed_and_release_lock(self, target_id: int, error: str) -> None:
        """Mark object as unprocessable."""
        stmt = sa.update(db_models.QueueInputMedia).values(
            lock=None,
            error=error,
        ).where(
            db_models.QueueInputMedia.id == target_id
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def delete(self, target_id: int) -> None:
        """Delete specific object."""
        stmt = sa.delete(db_models.QueueInputMedia).where(
            db_models.QueueInputMedia.id == target_id
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)
