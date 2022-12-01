# -*- coding: utf-8 -*-
"""Worker class.
"""
from typing import Optional

from omoide.daemons.worker import cfg
from omoide.daemons.worker.db import Database
from omoide.infra.custom_logging import Logger


class Worker:
    """Worker class."""

    def __init__(self, config: cfg.Config) -> None:
        """Initialize instance."""
        self.config = config
        self.sleep_interval = float(config.max_interval)

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
        formula = {
            self.config.name: {
                'hot': self.config.save_hot,
                'cold': self.config.save_cold,
            }
        }

        media_ids = database.get_media_ids(
            formula=formula,
            limit=self.config.batch_size,
        )

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
            replication_formula: dict[str, dict[str, bool]],
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
        # TODO
        return False

    def process_filesystem_operation(
            self,
            logger: Logger,
            database: Database,
            operation_id: int,
    ) -> Optional[bool]:
        """Perform filesystem operation, return True on success."""
        # TODO
        return False
