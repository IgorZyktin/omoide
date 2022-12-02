# -*- coding: utf-8 -*-
"""Database tools for worker.
"""
from typing import Optional

import sqlalchemy as sa

from omoide import utils
from omoide.daemons.common.base_db import BaseDatabase
from omoide.storage.database import models


class Database(BaseDatabase):
    """Wrapper on SQL commands for worker."""

    def get_media_ids(
            self,
            formula: dict[str, bool],
            limit: int,
            max_attempts: int = 5,
    ) -> list[int]:
        """Extract media resources to save."""
        stmt = sa.select(
            models.Media.id
        ).where(
            ~models.Media.replication.contains(formula),
            models.Media.attempts < max_attempts,
        ).order_by(
            models.Media.id
        ).limit(
            limit
        )
        with self.engine.begin() as conn:
            response = conn.execute(stmt).fetchall()

        return [x for x, in response]

    def select_media(
            self,
            media_id: int,
    ) -> Optional[models.Media]:
        """Select Media for update."""
        result = self.session.query(
            models.Media
        ).with_for_update(
            skip_locked=True
        ).filter_by(
            id=media_id
        ).first()
        return result

    def drop_media(
            self,
            formula: dict[str, bool],
    ) -> int:
        """Delete fully downloaded media rows, return total amount."""
        stmt = sa.delete(
            models.Media
        ).where(
            models.Media.replication.contains(formula),
        )

        with self.engine.begin() as conn:
            response = conn.execute(stmt)

        return int(response.rowcount)

    def drop_manual_copies(self) -> int:
        """Delete complete copy operations, return total amount."""
        stmt = sa.delete(
            models.ManualCopy
        ).where(
            models.ManualCopy.status == 'done'
        )

        with self.engine.begin() as conn:
            response = conn.execute(stmt)

        return int(response.rowcount)

    def get_manual_copy_targets(
            self,
            limit: int,
    ) -> list[int]:
        """Extract operations to process."""
        stmt = sa.select(
            models.FilesystemOperation.id
        ).where(
            models.FilesystemOperation.processed_at == None,  # noqa
            models.FilesystemOperation.status == 'init',
        ).order_by(
            models.FilesystemOperation.id
        ).limit(
            limit
        )
        with self.engine.begin() as conn:
            response = conn.execute(stmt).fetchall()

        return [x for x, in response]

    def select_copy_operation(
            self,
            copy_id: int,
    ) -> Optional[models.ManualCopy]:
        """Select manual copy operation for update."""
        result = self.session.query(
            models.ManualCopy
        ).with_for_update(
            skip_locked=True
        ).filter_by(
            id=copy_id
        ).first()
        return result

    def create_media_from_copy(
            self,
            copy: models.ManualCopy,
            content: bytes,
    ) -> None:
        """Convert copy operation into media."""
        media = models.Media(
            owner_uuid=copy.owner_uuid,
            item_uuid=copy.target_uuid,
            target_folder=copy.target_folder,
            created_at=utils.now(),
            processed_at=None,
            content=content,
            ext=copy.ext,
            replication={},
            error='',
            attempts=0,
        )

        self.session.add(media)
