# -*- coding: utf-8 -*-
"""Worker class.
"""
import traceback
from typing import Iterator
from typing import Optional

from sqlalchemy.orm.attributes import flag_modified

from omoide import utils
from omoide.daemons.worker import cfg
from omoide.daemons.worker.db import Database
from omoide.daemons.worker.filesystem import Filesystem
from omoide.infra.custom_logging import Logger
from omoide.storage.database import models


class Worker:
    """Worker class."""

    def __init__(self, config: cfg.Config, filesystem: Filesystem) -> None:
        """Initialize instance."""
        self.config = config
        self.filesystem = filesystem
        self.sleep_interval = float(config.max_interval)

    def get_folders(self) -> Iterator[str]:
        """Return all folders where we plan to save anything."""
        if self.config.save_hot:
            yield self.config.hot_folder
        if self.config.save_cold:
            yield self.config.cold_folder

    @property
    def formula(self) -> dict[str, bool]:
        """Return formula of this worker."""
        return {
            f'{self.config.name}-hot': self.config.save_hot,
            f'{self.config.name}-cold': self.config.save_cold,
        }

    def adjust_interval(self, operations: int) -> float:
        """Change interval based on amount of operations done."""
        if operations:
            self.sleep_interval = self.config.min_interval
        else:
            self.sleep_interval = min((
                self.sleep_interval * self.config.warm_up_coefficient,
                self.config.max_interval,
            ))
        return self.sleep_interval

    def download_media(
            self,
            logger: Logger,
            database: Database,
    ) -> int:
        """Download media from the database, return True if did something."""
        media_ids = database.get_media_ids(
            formula=self.formula,
            limit=self.config.batch_size,
        )

        logger.debug('Got {} media records: {}', len(media_ids), media_ids)

        operations = 0
        for media_id in media_ids:
            done = self.process_media(logger, database, media_id)

            if done is None:
                logger.debug('Skipped downloading media {}', media_id)
            elif done:
                operations += done
                logger.debug('Downloaded media {}', media_id)

        return operations

    def process_media(
            self,
            logger: Logger,
            database: Database,
            media_id: int,
    ) -> Optional[int]:
        """Save single media record, return True on success."""
        with database.start_session() as session:
            # noinspection PyBroadException
            try:
                media = database.select_media(session, media_id)

                if media is None:
                    result = None
                else:
                    result = self._process_media(logger, media)
                    self._process_item(media)
            except Exception:
                result = 0
                logger.exception('Failed to download media {}', media_id)
                session.rollback()
            else:
                if result:
                    session.commit()

        return result

    def _process_media(
            self,
            logger: Logger,
            media: models.Media,
    ) -> int:
        """Save single media record."""
        if not media.ext or not media.content:
            return 0

        for folder in self.get_folders():
            path = self.filesystem.ensure_folder_exists(
                logger,
                folder,
                media.target_folder,
                str(media.owner_uuid),
                str(media.item_uuid)[:self.config.prefix_size],
            )
            filename = f'{media.item_uuid}.{media.ext or ""}'
            self.filesystem.safely_save(logger, path, filename, media.content)

        media.attempts += 1
        media.processed_at = utils.now()
        media.replication.update(self.formula)
        flag_modified(media, 'replication')
        return 1

    @staticmethod
    def _process_item(media: models.Media) -> None:
        """Store changes in item description."""
        if media.target_folder == 'content':
            media.item.content_ext = media.ext
            media.item.metainfo.content_size = len(media.content or 0)
        elif media.target_folder == 'preview':
            media.item.preview_ext = media.ext
            media.item.metainfo.preview_size = len(media.content or 0)
        else:
            media.item.thumbnail_ext = media.ext
            media.item.metainfo.thumbnail_size = len(media.content or 0)

        media.item.metainfo.updated_at = utils.now()

    def drop_media(
            self,
            logger: Logger,
            database: Database,
    ) -> int:
        """Delete media from the DB, return amount of rows affected."""
        logger.debug('Dropping all media that fits into formula: {}',
                     self.config.replication_formula)

        dropped = database.drop_media(self.config.replication_formula)

        if dropped:
            logger.debug('Dropped {} rows with media', dropped)

        return dropped

    def manual_copy(
            self,
            logger: Logger,
            database: Database,
    ) -> int:
        """Perform manual copy operations."""
        targets = database.get_manual_copy_targets(self.config.batch_size)

        logger.debug('Got {} items to copy: {}', len(targets), targets)

        operations = 0
        for copy_id in targets:
            done = self.process_copying(logger, database, copy_id)

            if done is None:
                logger.debug('Skipped copy for id {}', copy_id)
            elif done:
                operations += done
                logger.debug('Copied id {}', copy_id)

        return operations

    def process_copying(
            self,
            logger: Logger,
            database: Database,
            copy_id: int,
    ) -> Optional[int]:
        """Perform filesystem operation, return True on success."""
        result = None
        with database.start_session() as session:
            # noinspection PyBroadException
            try:
                copy = database.select_copy_operation(session, copy_id)

                if copy is not None:
                    # noinspection PyBroadException
                    try:
                        media = self._process_copy(database, copy)
                        copy.status = 'done'
                        session.add(media)
                        result = 1
                    except Exception:
                        logger.exception('Failed to copy {}', copy_id)
                        result = 0
                        copy.status = 'fail'
                        copy.error += traceback.format_exc()
                    finally:
                        copy.processed_at = utils.now()

            except Exception:
                logger.exception('Failed to save changes in copy {}', copy_id)
                session.rollback()
                result = 0
            else:
                if result:
                    session.commit()

        return result

    def _process_copy(
            self,
            database: Database,
            copy: models.ManualCopy,
    ) -> models.Media:
        """Perform filesystem operation."""
        folder = self.config.hot_folder or self.config.cold_folder
        bucket = utils.get_bucket(copy.source_uuid, self.config.prefix_size)

        content = self.filesystem.load_from_filesystem(
            folder,
            str(copy.target_folder),
            str(copy.owner_uuid),
            bucket,
            f'{copy.source_uuid}.{(copy.ext or "").lower()}'
        )

        return database.create_media_from_copy(copy, content)

    @staticmethod
    def drop_manual_copies(
            logger: Logger,
            database: Database,
    ) -> int:
        """Delete thumbnails from the DB, return amount of rows affected."""
        dropped = database.drop_manual_copies()

        if dropped:
            logger.debug('Dropped {} rows with manual copies', dropped)

        return dropped
