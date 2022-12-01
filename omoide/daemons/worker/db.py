# -*- coding: utf-8 -*-
"""Database tools for worker.
"""
from omoide.daemons.common.base_db import BaseDatabase


class Database(BaseDatabase):
    """Wrapper on SQL commands for worker."""

    def download_media(
            self,
            formula: dict[str, dict[str, bool]],
            limit: int,
    ) -> list:
        """Extract media resources to save."""
        # TODO
        return []

    def download_filesystem_operations(
            self,
            limit: int,
    ) -> list:
        """Extract operations to process."""
        # TODO
        return []

    def drop_media(
            self,
            replication_formula: dict[str, dict[str, bool]],
    ) -> int:
        """Delete fully downloaded media rows, return total amount."""
        # TODO
        return 0
