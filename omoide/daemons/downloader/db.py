# -*- coding: utf-8 -*-
"""Wrapper on SQL commands for downloader."""
import contextlib
import sys
from typing import Optional, Iterator
from uuid import UUID

import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import utils
from omoide.daemons.downloader import cfg
from omoide.storage.database import models


class Database:
    """Wrapper on SQL commands for downloader."""
    _location_cache: dict[UUID, str] = {}

    def __init__(self, config: cfg.DownloaderConfig) -> None:
        """Initialize instance."""
        self.config = config
        self._engine: Optional[Engine] = None
        self._session: Optional[Session] = None

    @property
    def engine(self) -> Engine:
        """Engine getter."""
        if self._engine is None:
            raise RuntimeError('You must use life_cycle context manager')
        return self._engine

    @engine.setter
    def engine(self, new_engine: Engine) -> None:
        """Engine setter."""
        self._engine = new_engine

    @property
    def session(self) -> Session:
        """Session getter."""
        if self._session is None:
            raise RuntimeError('You must use start_session context manager')
        return self._session

    @session.setter
    def session(self, new_session: Optional[Session]) -> None:
        """Session setter."""
        self._session = new_session

    @contextlib.contextmanager
    def life_cycle(self):
        """Ensure tact connection is closed at the end."""
        self.engine = sqlalchemy.create_engine(
            self.config.db_url.get_secret_value(),
            echo=False,
            pool_pre_ping=True,
        )

        try:
            yield
        finally:
            self.engine.dispose()

    @contextlib.contextmanager
    def start_session(self):
        """Wrapper around SA session."""
        with Session(self.engine) as session:
            self.session = session
            yield
            self.session = None

    def get_media_to_download(self) -> Iterator[models.Media]:
        """Load all media rows with batching."""
        if self.config.limit == -1:
            limit = sys.maxsize
        else:
            limit = self.config.limit

        last_seen_uuid = None
        last_seen_type = None
        processed = 0

        while processed < limit:
            batch_size = min(self.config.batch_size, limit - processed)
            candidates = self.get_next_media_batch(batch_size,
                                                   last_seen_uuid,
                                                   last_seen_type)

            if not candidates:
                break

            yield from candidates
            processed += len(candidates)
            last_seen_uuid = candidates[-1].item_uuid
            last_seen_type = candidates[-1].media_type

    def get_next_media_batch(
            self,
            limit: int,
            last_seen_uuid: Optional[UUID],
            last_seen_type: Optional[str],
    ) -> list[models.Media]:
        """Load new batch of models."""
        query = self.session.query(
            models.Media
        ).where(
            models.Media.status == 'init',
        ).order_by(
            models.Media.created_at,
            models.Media.item_uuid,
            models.Media.media_type,
        )

        if last_seen_uuid is not None and last_seen_type is not None:
            query = query.where(
                sqlalchemy.tuple_(models.Media.item_uuid,
                                  models.Media.media_type)
                > sqlalchemy.tuple_(last_seen_uuid, last_seen_type),
            )

        if limit > 0:
            query = query.limit(limit)

        return query.all()

    def consider_media_as_done(
            self,
            media: models.Media,
    ) -> None:
        """Perform all operations when download is complete."""
        media.status = 'done'
        media.content = b''
        media.processed_at = utils.now()

        if media.media_type == 'content':
            media.item.content_ext = media.ext
        elif media.media_type == 'preview':
            media.item.preview_ext = media.ext
        elif media.media_type == 'thumbnail':
            media.item.thumbnail_ext = media.ext
        else:
            # TODO: replace it with proper logger call
            print(f'Unknown media type: {media.type!r}')

        self.session.commit()

    def consider_media_as_failed(
            self,
            media: models.Media,
    ) -> None:
        """Perform all operations when download is failed."""
        media.status = 'fail'
        media.processed_at = utils.now()
        self.session.commit()

    def finalize_media(
            self,
            media: models.Media,
            result: str,
    ) -> None:
        """Mark media as done or failed."""
        if result == 'done':
            self.consider_media_as_done(media)
        else:
            self.consider_media_as_failed(media)

    def get_cached_location_for_an_item(self, item_uuid: UUID) -> str:
        """Fast location load."""
        location = self._location_cache.get(item_uuid)

        if location is None:
            location = self.get_location_for_an_item(item_uuid)
            self._location_cache[item_uuid] = location

        return location

    def get_location_for_an_item(self, item_uuid: UUID) -> str:
        """Get human-readable location of an item."""
        current_uuid = item_uuid
        segments = []
        done_steps = 0
        max_steps = 100

        while current_uuid:
            done_steps += 1
            item = self.session.query(models.Item).get(current_uuid)
            current_uuid = item.parent_uuid
            segments.append(item.name or str(item.uuid))

            if done_steps > max_steps:
                # TODO: replace it with proper logger call
                print('Got into loop during parent search')
                break

        if not segments:
            return '???'

        return '/'.join(reversed(segments))
