# -*- coding: utf-8 -*-
"""Downloader implementation.
"""
import os
import random
from pathlib import Path
from typing import Optional
from uuid import UUID

import sqlalchemy
from sqlalchemy.engine import Engine

from omoide import jobs
from omoide import utils
from omoide.storage.database import models


def get_media(
        engine: Engine,
        limit: int,
        last_seen: Optional[tuple[UUID, str]] = None,
) -> list[tuple[UUID, str]]:
    """Return UUIDs of media records to save."""
    stmt = sqlalchemy.select(
        models.Media.item_uuid,
        models.Media.media_type,
    ).where(
        models.Media.status == 'init',
    )

    if last_seen is not None:
        last_uuid, last_type = last_seen
        stmt = stmt.where(
            (models.Media.item_uuid,
             models.Media.media_type) > (last_uuid, last_type),
        )

    stmt = stmt.order_by(
        models.Media.item_uuid,
        models.Media.media_type,
    )

    if limit > 0:
        stmt = stmt.limit(limit)

    with engine.begin() as conn:
        response = conn.execute(stmt)

    return [x for x in response]


def process_single_media(
        config: jobs.JobConfig,
        media: models.Media,
) -> str:
    """Perform all operations on single entry and return result."""
    if any((
            not media.media_type,
            not media.ext,
            not media.content,
    )):
        return 'bad-content'

    if config.dry_run:
        return 'ok'

    if config.copy_all or media.type == 'thumbnail':
        download_file_for_media(media, path=Path(config.hot_folder))

    download_file_for_media(media, path=Path(config.cold_folder))
    return 'ok'


def download_file_for_media(media: models.Media, path: Path) -> None:
    """Perform actual filesystem operations for media."""
    bucket = utils.get_bucket(media.item_uuid)
    filename = jobs.create_folders_for_filename(
        path,
        str(media.item.owner_uuid),
        media.media_type,
        bucket,
        f'{media.item_uuid}.{media.ext}'
    )

    temp_filename = filename + '.tmp' + str(random.randint(1, 1000))

    jobs.drop_if_exists(filename)
    jobs.drop_if_exists(temp_filename)

    with open(temp_filename, 'wb') as file:
        file.write(media.content)
        file.flush()
        os.fsync(file.fileno())

    os.rename(temp_filename, filename)


def consider_media_as_done(media: models.Media) -> None:
    """Perform all operations when download is complete."""
    media.status = 'done'
    media.content = b''
    media.processed_at = utils.now()

    if media.media_type == 'content':
        media.item.content_ext = media.ext
    elif media.media_type == 'preview':
        media.item.preview_ext = media.ext
    elif media.media_type == 'thumbnail':
        media.item.thumbnail_ext = media.ext
    else:
        # TODO: replace it with proper logger call
        print(f'Unknown media type: {media.type!r}')


def consider_media_as_failed(
        media: models.Media,
) -> None:
    """Perform all operations when download is failed."""
    media.status = 'fail'
    media.processed_at = utils.now()


def finalize_media(
        media: models.Media,
        result: str,
) -> None:
    """Mark media as done or failed."""
    if result == 'ok':
        consider_media_as_done(media)
    elif result == 'exc':
        consider_media_as_failed(media)
    else:
        consider_media_as_failed(media)
