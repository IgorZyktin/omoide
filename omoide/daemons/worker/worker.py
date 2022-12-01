# -*- coding: utf-8 -*-
"""Worker class.
"""
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

    def adjust_interval(self, did_something: bool) -> None:
        """Change interval based on previous actions."""
        if did_something:
            self.sleep_interval = self.config.min_interval
        else:
            self.sleep_interval = min((
                self.sleep_interval * self.config.warm_up_coefficient,
                self.config.max_interval,
            ))

    def download_media(
            self,
            logger: Logger,
            database: Database,
    ) -> bool:
        """Download media from the database, return True if did something."""
        media_ids = database.get_media_ids(
            formula=self.formula,
            limit=self.config.batch_size,
        )

        logger.debug('Got {} media records: {}', len(media_ids), media_ids)

        did_something = False
        for media_id in media_ids:
            did_something_more = self.process_media(logger, database, media_id)
            did_something = did_something or bool(did_something_more)

            if did_something is None:
                logger.debug('Skipped downloading media {}', media_id)
            elif did_something:
                logger.debug('Downloaded media {}', media_id)
            else:
                logger.error('Failed to download media {}', media_id)

        return bool(did_something)

    @staticmethod
    def delete_media(
            logger: Logger,
            database: Database,
            replication_formula: dict[str, bool],
    ) -> bool:
        """Delete media from the database, return True if did something."""
        dropped = database.drop_media(replication_formula)

        if dropped:
            logger.debug('Dropped {} rows', dropped)

        return dropped != 0

    def process_filesystem_operations(
            self,
            logger: Logger,
            database: Database,
    ) -> bool:
        """Perform filesystem operations, return True if did something."""
        operations = database.get_filesystem_operations(
            limit=self.config.batch_size,
        )

        logger.debug('Got {} operations: {}', len(operations), operations)

        did_something = False
        for operation_id in operations:
            did_something_more = self.process_filesystem_operation(
                logger, database, operation_id)
            did_something = did_something or bool(did_something_more)

            if did_something is None:
                logger.debug('Skipped processing operation {}', operation_id)
            elif did_something:
                logger.debug('Processed operation {}', operation_id)
            else:
                logger.error('Failed to process operation {}', operation_id)

        return bool(did_something)

    def process_media(
            self,
            logger: Logger,
            database: Database,
            media_id: int,
    ) -> Optional[bool]:
        """Save single media record, return True on success."""
        with database.start_session():
            # noinspection PyBroadException
            try:
                media = database.select_media(media_id)

                if media is None:
                    result = None
                else:
                    self._process_media(logger, media)
                    result = True
            except Exception:
                result = False
                logger.exception('Failed to handle media {}', media_id)
                database.session.rollback()
            else:
                database.session.commit()

        return result

    def _process_media(
            self,
            logger: Logger,
            media: models.Media,
    ) -> None:
        """Save single media record."""
        if not media.ext or not media.content:
            return

        for folder in self.get_folders():
            path = self.filesystem.ensure_folder_exists(
                logger,
                folder,
                media.media_type,
                str(media.owner_uuid),
                str(media.owner_uuid)[:self.config.prefix_size],
            )
            filename = f'{media.item_uuid}.{media.ext}'
            self.filesystem.safely_save(logger, path, filename, media.content)

        media.attempts += 1
        media.processed_at = utils.now()
        media.replication.update(self.formula)
        flag_modified(media, 'replication')

    def process_filesystem_operation(
            self,
            logger: Logger,
            database: Database,
            operation_id: int,
    ) -> Optional[bool]:
        """Perform filesystem operation, return True on success."""
        with database.start_session():
            # noinspection PyBroadException
            try:
                operation = database.select_filesystem_operation(
                    operation_id)

                if operation is None:
                    result = None
                else:
                    self._process_filesystem_operation(logger, operation)
                    result = True
            except Exception:
                result = False
                logger.exception('Failed to handle operation {}',
                                 operation_id)
                database.session.rollback()
            else:
                database.session.commit()

        return result

    def _process_filesystem_operation(
            self,
            logger: Logger,
            operation: models.FilesystemOperation,
    ) -> None:
        """Perform filesystem operation."""
        # TODO
