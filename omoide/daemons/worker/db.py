# -*- coding: utf-8 -*-
"""Database tools for worker.
"""
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from omoide import utils
from omoide.commands.common.base_db import BaseDatabase
from omoide.daemons.worker import cfg
from omoide.daemons.worker.filesystem import Filesystem
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
            ~models.Media.replication.contains(formula),  # noqa
            models.Media.attempts < max_attempts,
            models.Media.error == '',
        ).order_by(
            models.Media.id
        ).limit(
            limit
        )
        with self.engine.begin() as conn:
            response = conn.execute(stmt).fetchall()

        return [x for x, in response]

    @staticmethod
    def select_media(
            session: Session,
            media_id: int,
    ) -> Optional[models.Media]:
        """Select Media for update."""
        result = session.query(
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
            models.Media.replication.contains(formula),  # noqa
        )

        with self.engine.begin() as conn:
            response = conn.execute(stmt)

        return int(response.rowcount)

    def get_manual_copy_targets(
            self,
            limit: int,
    ) -> list[int]:
        """Extract copy operations to process."""
        stmt = sa.select(
            models.ManualCopy.id
        ).where(
            models.ManualCopy.processed_at == None,  # noqa
            models.ManualCopy.status == 'init',
        ).order_by(
            models.ManualCopy.id
        ).limit(
            limit
        )
        with self.engine.begin() as conn:
            response = conn.execute(stmt).fetchall()

        return [x for x, in response]

    @staticmethod
    def select_copy_operation(
            session: Session,
            copy_id: int,
    ) -> Optional[models.ManualCopy]:
        """Select manual copy operation for update."""
        result = session.query(
            models.ManualCopy
        ).with_for_update(
            skip_locked=True
        ).filter_by(
            id=copy_id
        ).first()
        return result

    @staticmethod
    def create_media_from_copy(
            copy: models.ManualCopy,
            content: bytes,
    ) -> models.Media:
        """Convert copy operation into media."""
        return models.Media(
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

    def mark_origin(
            self,
            copy: models.ManualCopy,
    ) -> None:
        """Convert copy operation into media."""
        stmt = sa.update(
            models.Metainfo
        ).where(
            models.Metainfo.item_uuid == copy.target_uuid
        ).values(
            extras=sa.func.jsonb_set(
                models.Metainfo.extras,
                '{copied_cover_from}',
                f'"{copy.source_uuid}"',
            )
        )
        self.engine.execute(stmt)

    def copy_content_parameters(
            self,
            config: cfg.Config,
            filesystem: Filesystem,
            session: Session,
            copy: models.ManualCopy,
    ) -> None:
        """Copy width and height from origin."""
        source_item = session.query(
            models.Item
        ).filter(
            models.Item.uuid == copy.source_uuid
        ).first()

        target_item = session.query(
            models.Item
        ).filter(
            models.Item.uuid == copy.target_uuid
        ).first()

        source_metainfo = session.query(
            models.Metainfo
        ).filter(
            models.Metainfo.item_uuid == copy.source_uuid
        ).first()

        target_metainfo = session.query(
            models.Metainfo
        ).filter(
            models.Metainfo.item_uuid == copy.target_uuid
        ).first()

        if not all((source_item,
                    target_item,
                    source_metainfo,
                    target_metainfo)):
            return

        folder = config.hot_folder or config.cold_folder
        bucket = utils.get_bucket(copy.source_uuid, config.prefix_size)

        size = filesystem.get_size(
            folder,
            str(copy.target_folder),
            str(copy.owner_uuid),
            bucket,
            f'{copy.source_uuid}.{(copy.ext or "").lower()}'
        )

        if copy.target_folder == 'content':
            target_metainfo.content_size = size
            target_metainfo.content_width = source_metainfo.content_width
            target_metainfo.content_height = source_metainfo.content_height
            target_item.content_ext = source_item.content_ext

        elif copy.target_folder == 'preview':
            target_metainfo.preview_size = size
            target_metainfo.preview_width = source_metainfo.preview_width
            target_metainfo.preview_height = source_metainfo.preview_height
            target_item.preview_ext = source_item.preview_ext

        elif copy.target_folder == 'thumbnail':
            target_metainfo.thumbnail_size = size
            target_metainfo.thumbnail_width = source_metainfo.thumbnail__width
            target_metainfo.thumbnail_height = source_metainfo.thumbnail_height
            target_item.thumbnail_ext = source_item.thumbnail_ext

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
