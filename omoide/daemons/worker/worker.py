# -*- coding: utf-8 -*-
"""Worker class.
"""
from omoide.daemons.worker import cfg


class Worker:
    """Worker class."""

    def __init__(self, config: cfg.Config) -> None:
        """Initialize instance."""
        self.config = config
