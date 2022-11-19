# -*- coding: utf-8 -*-
"""Refresh size command.
"""
from pathlib import Path
from typing import Iterator
from typing import NamedTuple
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from omoide.commands.common import helpers
from omoide.commands.refresh_size.cfg import Config
from omoide.storage.database import models


class Pack(NamedTuple):
    """Data transfer object."""
    uuid: UUID
    owner_uuid: UUID
    content_ext: Optional[str]
    preview_ext: Optional[str]
    thumbnail_ext: Optional[str]


def get_metainfo(
        config: Config,
        session: Session,
) -> Iterator[tuple[UUID, UUID, Optional[str], Optional[str], Optional[str]]]:
    """Get every item with some content."""
    stmt = sa.select(
        models.Metainfo.item_uuid,
        models.Item.owner_uuid,
        models.Item.content_ext,
        models.Item.preview_ext,
        models.Item.thumbnail_ext,
    ).join(
        models.Item,
        models.Item.uuid == models.Metainfo.item_uuid,
    ).where(
        sa.or_(
            models.Item.content_ext != None,  # noqa
            models.Item.preview_ext != None,  # noqa
            models.Item.thumbnail_ext != None,  # noqa
        )
    )

    if config.marker is not None:
        stmt = stmt.where(
            models.Metainfo.item_uuid > str(config.marker)
        )

    stmt = stmt.order_by(models.Metainfo.item_uuid)

    if config.limit != -1:
        stmt = stmt.limit(config.limit)

    return session.execute(stmt)


def update_size(
        config: Config,
        metainfo: models.Metainfo,
        target: Pack,
        base: Path,
) -> int:
    """Get actual file size."""
    prefix = helpers.get_prefix(target.uuid, config.prefix_size)

    changed = 0
    for each in ['content', 'preview', 'thumbnail']:
        ext = getattr(target, f'{each}_ext')
        if ext:
            path = (base
                    / each
                    / str(target.owner_uuid)
                    / prefix
                    / f'{target.uuid}.{ext}')
            size = get_size(path)

            if size is not None:
                setattr(metainfo, f'{each}_size', size)
                changed += 1

    return changed


def get_size(path: Path) -> Optional[int]:
    """Get size of the file in bytes."""
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return None
