# -*- coding: utf-8 -*-
"""Wrapper on SQL commands for downloader."""
import contextlib

from omoide.daemons.downloader import cfg


class Database:
    """Wrapper on SQL commands for downloader."""

    def __init__(self, config: cfg.DownloaderConfig) -> None:
        """Initialize instance."""
        self.config = config

    @contextlib.contextmanager
    def life_cycle(self):
        """Ensure tact connection is closed at the end."""
        try:
            yield
        finally:
            pass
