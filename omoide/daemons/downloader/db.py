# -*- coding: utf-8 -*-
"""Wrapper on SQL commands for downloader."""
import contextlib
from typing import Optional

import sqlalchemy
from sqlalchemy.engine import Engine

from omoide.daemons.downloader import cfg
from omoide.storage.database import models


class Database:
    """Wrapper on SQL commands for downloader."""

    def __init__(self, config: cfg.DownloaderConfig) -> None:
        """Initialize instance."""
        self.config = config
        self._engine: Optional[Engine] = None

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

    def get_media_to_download(self) -> list[models.Media]:
        """Load new batch of models."""
