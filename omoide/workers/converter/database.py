"""Storage implementation."""

from collections.abc import Sequence

import sqlalchemy as sa

from omoide import const
from omoide import models
from omoide.database import db_models
from omoide.workers.common.database import PostgreSQLDatabase


class ConverterPostgreSQLDatabase(PostgreSQLDatabase):
    """Storage in database."""

    def get_input_media_candidates(
        self,
        batch_size: int,
        content_types: Sequence[str],
    ) -> list[int]:
        """Return candidates to operate on."""
        query = (
            sa.select(db_models.QueueInputMedia.id)
            .where(
                db_models.QueueInputMedia.lock == sa.null(),
                db_models.QueueInputMedia.error == sa.null(),
                db_models.QueueInputMedia.content_type.in_(content_types),
            )
            .order_by(db_models.QueueInputMedia.id)
            .limit(batch_size)
        )

        with self.engine.begin() as conn:
            response = conn.execute(query).all()

        return [x for (x,) in response]

    def lock_input_media(self, target_id: int, name: str) -> bool:
        """Lock specific object."""
        stmt = (
            sa.update(db_models.QueueInputMedia)
            .values(
                lock=name,
            )
            .where(
                db_models.QueueInputMedia.id == target_id,
                db_models.QueueInputMedia.lock == sa.null(),
            )
        )

        with self.engine.begin() as conn:
            response = conn.execute(stmt)

        return bool(response.rowcount)

    def get_input_media(self, target_id: int) -> models.InputMedia:
        """Load data from storage."""
        query = sa.select(db_models.QueueInputMedia).where(
            db_models.QueueInputMedia.id == target_id
        )

        with self.engine.begin() as conn:
            response = conn.execute(query).one()

        return models.InputMedia(
            id=response.id,
            user_uuid=response.user_uuid,
            item_uuid=response.item_uuid,
            created_at=response.created_at,
            ext=response.ext,
            content_type=response.content_type,
            extras=response.extras,
            error=response.error,
            content=response.content,
        )

    def save_output_media(
        self, model: models.InputMedia, media_type: str
    ) -> None:
        """Save data to storage."""
        content = model.content
        if len(content) >= const.LARGE_OBJECT_SIZE:
            oid = self.save_large_object(model.content)
            model.extras['oid'] = oid
            content = b''
        else:
            model.extras['oid'] = None

        stmt = sa.insert(db_models.QueueOutputMedia).values(
            user_uuid=model.user_uuid,
            item_uuid=model.item_uuid,
            created_at=model.created_at,
            ext=model.ext,
            content_type=model.content_type,
            media_type=media_type,
            extras=model.extras,
            error=model.error,
            content=content,
            processed_by=[],
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def mark_failed_and_release_lock(self, target_id: int, error: str) -> None:
        """Mark object as unprocessable."""
        stmt = (
            sa.update(db_models.QueueInputMedia)
            .values(
                lock=None,
                error=error,
            )
            .where(db_models.QueueInputMedia.id == target_id)
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def delete_media(self, target_id: int) -> None:
        """Delete specific object."""
        stmt = sa.delete(db_models.QueueInputMedia).where(
            db_models.QueueInputMedia.id == target_id
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)
