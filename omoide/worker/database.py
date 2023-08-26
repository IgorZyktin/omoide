"""Database helper class for Worker.
"""
import contextlib
from typing import Generator

import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import utils
from omoide.infra import custom_logging
from omoide.storage.database import db_models

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
        self._session: Session | None = None

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
            self._session = session
            yield session
            self._session = None

    @property
    def session(self) -> Session:
        """Return current session."""
        if self._session is None:
            msg = 'You need to start session before using it'
            raise RuntimeError(msg)
        return self._session

    def get_thumbnail_batch(
            self,
            batch_size: int,
            last_seen: int | None,
    ) -> list[db_models.CommandCopyThumbnail]:
        """Return list of thumbnails to copy."""
        query = self.session.query(db_models.CommandCopyThumbnail)

        if last_seen is not None:
            query = query.filter(
                db_models.CommandCopyThumbnail.id > last_seen
            )

        query = query.order_by(
            db_models.CommandCopyThumbnail.id,
        ).limit(batch_size)

        return query.all()

    def get_media_batch(
            self,
            batch_size: int,
            last_seen: int | None,
    ) -> list[db_models.Media]:
        """Return list of media records to download."""
        query = self.session.query(db_models.Media)

        if last_seen is not None:
            query = query.filter(
                db_models.Media.id > last_seen
            )

        query = query.order_by(
            db_models.Media.id,
        ).limit(batch_size)

        return query.all()

    @staticmethod
    def create_media_from_copy(
            command: db_models.CommandCopyThumbnail,
            content: bytes,
    ) -> db_models.Media:
        """Convert copy operation into media."""
        # FIXME - alter signature of the Media
        return db_models.Media(
            owner_uuid=command.owner_uuid,
            item_uuid=command.target_uuid,
            target_folder='thumbnail',
            created_at=utils.now(),
            processed_at=None,
            content=content,
            ext=command.ext,
            replication={},
            error='',
            attempts=0,
        )

    def mark_origin_of_thumbnail(
            self,
            thumbnail: db_models.CommandCopyThumbnail,
    ) -> None:
        """Mark where item got its thumbnail."""
        stmt = sa.update(
            db_models.Metainfo
        ).where(
            db_models.Metainfo.item_uuid == thumbnail.target_uuid
        ).values(
            extras=sa.func.jsonb_set(
                db_models.Metainfo.extras,
                ['copied_thumbnail_from'],
                f'"{thumbnail.source_uuid}"',
            )
        )
        self.session.execute(stmt)

    def copy_thumbnail_parameters(
            self,
            command: db_models.CommandCopyThumbnail,
            size: int,
    ) -> None:
        """Copy width/height from origin."""
        source = self.session.query(db_models.Item).get(command.source_uuid)

        if not source:
            msg = (f'Source item {command.source_uuid} does not exist, '
                   f'cannot copy thumbnail for {command.id}')
            raise RuntimeError(msg)

        target = self.session.query(db_models.Item).get(command.target_uuid)

        if not target:
            msg = (f'Target item {command.source_uuid} does not exist, '
                   f'cannot copy thumbnail for {command.id}')
            raise RuntimeError(msg)

        target.metainfo.thumbnail_size = size
        target.metainfo.thumbnail_width = source.metainfo.thumbnail_width
        target.metainfo.thumbnail_height = source.metainfo.thumbnail_height
        target.metainfo.media_type = source.metainfo.media_type
        target.thumbnail_ext = source.thumbnail_ext

    def drop_media(self) -> int:
        """Delete fully downloaded media rows, return total amount."""
        stmt = sa.delete(
            db_models.Media
        ).where(
            db_models.Media.processed_at != None,  # noqa
            db_models.Media.error == '',
        )

        with self._engine.begin() as conn:
            response = conn.execute(stmt)

        return int(response.rowcount)

    def drop_thumbnail_copies(self) -> int:
        """Delete complete copy operations, return total deleted amount."""
        stmt = sa.delete(
            db_models.CommandCopyThumbnail
        ).where(
            db_models.CommandCopyThumbnail.processed_at != None,  # noqa
            db_models.CommandCopyThumbnail.error != '',
        )

        with self._engine.begin() as conn:
            response = conn.execute(stmt)

        return int(response.rowcount)
