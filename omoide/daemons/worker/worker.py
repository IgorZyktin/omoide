# -*- coding: utf-8 -*-
"""Worker class.
"""
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

    def download_media(self, logger: Logger, database: Database) -> bool:
        """Download media from the database, return True if did something."""
        # TODO
        return False

    def delete_media(self, logger: Logger, database: Database) -> bool:
        """Delete media from the database, return True if did something."""
        # TODO
        return False
