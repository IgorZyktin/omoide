"""Database helper class for Worker.
"""
import contextlib
from typing import Generator

import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import utils
from omoide.infra import custom_logging
from omoide.storage.database import models as db_models
from omoide.worker.filesystem import Filesystem
from omoide.worker.worker_config import Config

LOG = custom_logging.get_logger(__name__)


class Database:
    """Database helper class for Worker."""

    def __init__(self, db_uri: str, echo: bool) -> None:
        """Initialize instance."""
        self._db_uri = db_uri
        self._engine = sa.create_engine(
            self._db_uri,
            echo=echo,
            pool_pre_ping=True,
        )

    @contextlib.contextmanager
    def life_cycle(self) -> Generator[Engine, None, None]:
        """Ensure that connection is closed at the end."""
        try:
            yield self._engine
        finally:
            self._engine.dispose()

    @contextlib.contextmanager
    def start_session(self) -> Generator[Session, None, None]:
        """Wrapper around SA session."""
        with Session(self._engine) as session:
            yield session

    def get_media_ids(self, limit: int) -> list[int]:
        """Extract media resources to save."""
        stmt = sa.select(
            db_models.Media.id
        ).where(
            db_models.Media.error == '',
        ).order_by(
            db_models.Media.id
        ).limit(
            limit
        )
        with self._engine.begin() as conn:
            response = conn.execute(stmt).fetchall()

        return [x for x, in response]

    @staticmethod
    def get_media(
            session: Session,
            media_id: int,
    ) -> db_models.Media | None:
        """Select Media for update."""
        return session.query(
            db_models.Media
        ).filter_by(
            id=media_id
        ).first()

    def drop_media(self) -> int:
        """Delete fully downloaded media rows, return total amount."""
        stmt = sa.delete(
            db_models.Media
        ).where(
            db_models.Media.error == '',
        )

        with self._engine.begin() as conn:
            response = conn.execute(stmt)

        return int(response.rowcount)

    def get_manual_copy_targets(self, limit: int) -> list[int]:
        """Extract copy operations to process."""
        stmt = sa.select(
            db_models.ManualCopy.id
        ).where(
            db_models.ManualCopy.processed_at == None,  # noqa
            db_models.ManualCopy.status == 'init',
        ).order_by(
            db_models.ManualCopy.id
        ).limit(
            limit
        )
        with self.engine.begin() as conn:
            response = conn.execute(stmt).fetchall()

        return [x for x, in response]

    @staticmethod
    def select_copy_operation(
            session: Session,
            copy_id: int,
    ) -> db_models.ManualCopy | None:
        """Select manual copy operation for update."""
        result = session.query(
            db_models.ManualCopy
        ).with_for_update(
            skip_locked=True
        ).filter_by(
            id=copy_id
        ).first()
        return result

    @staticmethod
    def create_media_from_copy(
            copy: db_models.ManualCopy,
            content: bytes,
    ) -> db_models.Media:
        """Convert copy operation into media."""
        return db_models.Media(
            owner_uuid=copy.owner_uuid,
            item_uuid=copy.target_uuid,
            target_folder=copy.target_folder,
            created_at=utils.now(),
            processed_at=None,
            content=content,
            ext=copy.ext,
            replication={},
            error='',
            attempts=0,
        )

    def mark_origin(self, copy: db_models.ManualCopy) -> None:
        """Convert copy operation into media."""
        stmt = sa.update(
            db_models.Metainfo
        ).where(
            db_models.Metainfo.item_uuid == copy.target_uuid
        ).values(
            extras=sa.func.jsonb_set(
                db_models.Metainfo.extras,
                ['copied_cover_from'],
                f'"{copy.source_uuid}"',
            )
        )
        self.engine.execute(stmt)

    @staticmethod
    def copy_content_parameters(
            config: Config,
            filesystem: Filesystem,
            session: Session,
            copy: db_models.ManualCopy,
    ) -> None:
        """Copy width and height from origin."""
        source_item = session.query(
            db_models.Item
        ).filter(
            db_models.Item.uuid == copy.source_uuid
        ).first()

        target_item = session.query(
            db_models.Item
        ).filter(
            db_models.Item.uuid == copy.target_uuid
        ).first()

        source_metainfo = session.query(
            db_models.Metainfo
        ).filter(
            db_models.Metainfo.item_uuid == copy.source_uuid
        ).first()

        target_metainfo = session.query(
            db_models.Metainfo
        ).filter(
            db_models.Metainfo.item_uuid == copy.target_uuid
        ).first()

        if source_item is None \
                or target_item is None \
                or source_metainfo is None \
                or target_metainfo is None:
            LOG.warning(
                'Got discrepancy in sources, '
                'source_item = {}'
                'target_item = {}'
                'source_metainfo = {}'
                'target_metainfo = {}',
                source_item,
                target_item,
                source_metainfo,
                target_metainfo
            )
            return

        folder = config.hot_folder or config.cold_folder
        bucket = utils.get_bucket(copy.source_uuid, config.prefix_size)

        size = filesystem.get_size(
            folder,
            str(copy.target_folder),
            str(copy.owner_uuid),
            bucket,
            f'{copy.source_uuid}.{(copy.ext or "").lower()}'
        )

        if copy.target_folder == 'content':
            target_metainfo.content_size = size
            target_metainfo.content_width = source_metainfo.content_width
            target_metainfo.content_height = source_metainfo.content_height
            target_item.content_ext = source_item.content_ext

        elif copy.target_folder == 'preview':
            target_metainfo.preview_size = size
            target_metainfo.preview_width = source_metainfo.preview_width
            target_metainfo.preview_height = source_metainfo.preview_height
            target_item.preview_ext = source_item.preview_ext

        elif copy.target_folder == 'thumbnail':
            target_metainfo.thumbnail_size = size
            target_metainfo.thumbnail_width = source_metainfo.thumbnail_width
            target_metainfo.thumbnail_height = source_metainfo.thumbnail_height
            target_item.thumbnail_ext = source_item.thumbnail_ext

        target_metainfo.media_type = source_metainfo.media_type

    def drop_manual_copies(self) -> int:
        """Delete complete copy operations, return total amount."""
        stmt = sa.delete(
            db_models.ManualCopy
        ).where(
            db_models.ManualCopy.status == 'done'
        )

        with self._engine.begin() as conn:
            response = conn.execute(stmt)

        return int(response.rowcount)
