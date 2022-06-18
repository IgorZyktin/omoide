# -*- coding: utf-8 -*-
"""Downloader implementation.
"""
import os
import random
from pathlib import Path

import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import jobs
from omoide import utils
from omoide.storage.database import models


def get_media(
        engine: Engine,
        max_attempts: int,
        limit: int,
        last_seen: int = -1,
) -> list[int]:
    """Return ids of media records to save."""
    stmt = sqlalchemy.select(
        models.Media.id
    ).where(
        models.Media.status == 'init',
        models.Media.id > last_seen,
        models.Media.attempts < max_attempts,
    ).order_by(
        models.Media.id
    )

    if limit > 0:
        stmt = stmt.limit(limit)

    with engine.begin() as conn:
        response = conn.execute(stmt)

    return [x for x, in response]


def process_single_media(
        config: jobs.JobConfig,
        media: models.Media,
) -> str:
    """Perform all operations on single entry and return result."""
    if any((
            not media.type,
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
        media.type,
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
    media.attempts += 1

    if media.type == 'content':
        media.item.content_ext = media.ext
    elif media.type == 'preview':
        media.item.preview_ext = media.ext
    elif media.type == 'thumbnail':
        media.item.thumbnail_ext = media.ext
    else:
        # TODO: replace it with proper logger call
        print(f'Unknown media type: {media.type!r}')


def consider_media_as_failed(
        session: Session,
        media: models.Media,
        retry: bool = True,
) -> None:
    """Perform all operations when download is failed."""
    media.status = 'fail'
    media.processed_at = utils.now()

    if retry:
        new_attempt = models.Media(
            item_uuid=media.item_uuid,
            created_at=media.created_at,
            processed_at=None,
            status='init',
            type=media.type,
            ext=media.ext,
            content=media.content,
            attempts=media.attempts + 1,
        )
        session.add(new_attempt)

    media.content = b''
    media.attempts += 1


def finalize_media(
        session: Session,
        media: models.Media,
        result: str,
) -> None:
    """Mark media as done or failed."""
    if result == 'ok':
        consider_media_as_done(media)
    elif result == 'exc':
        consider_media_as_failed(session, media, retry=True)
    else:
        consider_media_as_failed(session, media, retry=False)
