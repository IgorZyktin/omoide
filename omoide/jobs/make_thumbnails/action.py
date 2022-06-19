# -*- coding: utf-8 -*-
"""Database operations for make_thumbnails job.
"""
import os
import random
import shutil
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from omoide import utils, jobs
from omoide.jobs.common import filesystem
from omoide.storage.database import models


def get_item_without_thumbnail(
        session: Session,
        last_seen: int,
) -> Optional[models.Item]:
    """Return collection without cover."""
    return session.query(
        models.Item
    ).where(
        models.Item.is_collection,
        models.Item.thumbnail_ext == None,  # noqa: E711
        models.Item.number > last_seen,
    ).order_by(
        models.Item.number
    ).first()


def get_first_child_with_thumbnail(
        session: Session,
        item: models.Item,
) -> Optional[models.Item]:
    """Get first child with thumbnail for given item."""
    # TODO: what if specific user has no access to this item?
    child = session.query(
        models.Item
    ).where(
        models.Item.parent_uuid == item.uuid
    ).order_by(
        models.Item.number
    ).first()

    if child is None:
        return None

    if child.thumbnail_ext is None:
        # maybe it has own children with thumbnails
        return get_first_child_with_thumbnail(session, child)

    return child


def copy_thumbnail(
        config: jobs.JobConfig,
        parent: models.Item,
        child: models.Item,
) -> bool:
    """Perform thumbnail copy for single entry, return True on success."""
    if not child.thumbnail_ext:
        return False

    if config.dry_run:
        return True

    parent.thumbnail_ext = child.thumbnail_ext

    for path in [config.hot_folder, config.cold_folder]:
        copy_thumbnail_at_path(Path(path), parent, child)

    return True


def copy_thumbnail_at_path(
        path: Path,
        parent: models.Item,
        child: models.Item,
) -> None:
    """Perform copy operation on a specific path."""
    parent_bucket = utils.get_bucket(parent.uuid)
    child_bucket = utils.get_bucket(child.uuid)

    child_filename = filesystem.create_folders_for_filename(
        path,
        str(child.owner_uuid),
        'thumbnail',
        child_bucket,
        f'{child.uuid}.{child.thumbnail_ext}'
    )

    parent_filename = filesystem.create_folders_for_filename(
        path,
        str(parent.owner_uuid),
        'thumbnail',
        parent_bucket,
        f'{parent.uuid}.{parent.thumbnail_ext}'
    )

    temp_filename = child_filename + '.tmp' + str(random.randint(1, 1000))

    filesystem.drop_if_exists(parent_filename)
    filesystem.drop_if_exists(temp_filename)

    shutil.copyfile(child_filename, temp_filename)
    os.rename(temp_filename, parent_filename)
