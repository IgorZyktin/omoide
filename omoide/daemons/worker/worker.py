# -*- coding: utf-8 -*-
"""Worker class.
"""
from typing import Optional

from omoide import utils
from omoide.daemons.worker import cfg
from omoide.daemons.worker.db import Database
from omoide.infra.custom_logging import Logger
from omoide.storage.database import models


class Worker:
    """Worker class."""

    def __init__(self, config: cfg.Config) -> None:
        """Initialize instance."""
        self.config = config
        self.sleep_interval = float(config.max_interval)

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
                logger.debug('\tSkipped downloading media {}', media_id)
            elif did_something:
                logger.debug('\tDownloaded media {}', media_id)
            else:
                logger.error('\tFailed to download media {}', media_id)

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
                logger.debug('\tSkipped processing operation {}', operation_id)
            elif did_something:
                logger.debug('\tProcessed operation {}', operation_id)
            else:
                logger.error('\tFailed to process operation {}', operation_id)

        return bool(did_something)

    def process_media(
            self,
            logger: Logger,
            database: Database,
            media_id: int,
    ) -> Optional[bool]:
        """Save single media record, return True on success."""
        with database.start_session() as session:
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
                session.rollback()
            else:
                session.commit()

        return result

    def _process_media(
            self,
            logger: Logger,
            media: models.Media,
    ) -> None:
        """Save single media record."""
        media.processed_at = utils.now()
        media.replication.update(self.formula)

    def process_filesystem_operation(
            self,
            logger: Logger,
            database: Database,
            operation_id: int,
    ) -> Optional[bool]:
        """Perform filesystem operation, return True on success."""
        # TODO
        return False
