"""Move metainfo key to extras."""

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm.attributes import flag_modified

from omoide import custom_logging
from omoide.storage.database import db_models
from omoide.storage.database.sync_db import SyncDatabase

LOG = custom_logging.get_logger(__name__)


def run(database: SyncDatabase, key: str,
        batch_size: int, limit: int) -> None:
    """Move metainfo key to extras."""
    last_seen: UUID | None = None
    processed = 0
    running = True

    with database.start_session() as session:
        while running:
            query = session.query(
                db_models.Metainfo,
            ).filter(
                getattr(db_models.Metainfo, key) != sa.null()
            ).order_by(
                db_models.Metainfo.item_uuid
            )

            if last_seen is not None:
                query = query.filter(
                    db_models.Metainfo.item_uuid > last_seen
                )

            models = query.limit(batch_size).all()

            if not models:
                break

            for metainfo in models:
                LOG.info(f'Altered `{key}` for {metainfo.item_uuid}')
                metainfo.extras[key] = getattr(metainfo, key)
                setattr(metainfo, key, None)
                flag_modified(metainfo, 'extras')
                session.flush([metainfo])

                last_seen = metainfo.item_uuid
                processed += 1
                if 0 < limit <= processed:
                    running = False
                    break

        session.commit()

    LOG.info('Altered {} rows', processed)
