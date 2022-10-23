# -*- coding: utf-8 -*-
"""Downloader daemon.

Downloads processed images from database to the local storages(s).
We're using database as a medium.
"""
import os
import random
from pathlib import Path

from omoide import utils
from omoide.daemons.common import action_class
from omoide.daemons.common import out
from omoide.daemons.downloader import cfg
from omoide.daemons.downloader import db
from omoide.storage.database import models


def download_items_from_database_to_storages(
        config: cfg.DownloaderConfig,
        database: db.Database,
        output: out.Output,
) -> list[action_class.Action]:
    """Do the actual download job."""
    actions = []
    with database.start_session():
        batch = database.get_media_to_download()

        for media in batch:
            action = action_class.Action(status='work')

            try:
                size = len(media.content)
                if process_single_media(config, media):
                    action.done()
                else:
                    action.fail()
            except Exception as exc:
                action.fail()

                if config.strict:
                    raise

                # TODO: replace it with proper logger call
                print(f'{type(exc).__name__}: {exc}')

            action.ended_at = utils.now()
            actions.append(action)

            if not config.dry_run:
                database.finalize_media(media, action.status)

            location = database.get_cached_location_for_an_item(
                item_uuid=media.item_uuid,
            )

            output.print_row(
                processed_at=str(action.ended_at.replace(microsecond=0,
                                                         tzinfo=None)),
                uuid=str(media.item_uuid),
                type=str(media.media_type),
                size=utils.byte_count_to_text(size),
                status=action.status,
                location=utils.no_longer_than(' ' + location, 93),
            )

    return actions


def process_single_media(
        config: cfg.DownloaderConfig,
        media: models.Media,
) -> bool:
    """Save one object. Return True on success."""
    if any((
            not media.media_type,
            not media.ext,
            not media.content,
    )):
        return False

    if config.dry_run:
        return True

    if (config.copy_all or media.media_type == 'thumbnail') and config.use_hot:
        download_file_for_media(media, path=Path(config.hot_folder))

    download_file_for_media(media, path=Path(config.cold_folder))

    return True


def download_file_for_media(media: models.Media, path: Path) -> None:
    """Perform actual filesystem operations for media."""
    bucket = utils.get_bucket(media.item_uuid)
    filename = create_folders_for_filename(
        path,
        str(media.media_type),
        str(media.item.owner_uuid),
        bucket,
        f'{media.item_uuid}.{media.ext.lower()}'
    )

    temp_filename = filename + '.tmp' + str(random.randint(1, 1000))

    drop_if_exists(filename)
    drop_if_exists(temp_filename)

    with open(temp_filename, 'wb') as file:
        file.write(media.content)
        file.flush()
        os.fsync(file.fileno())

    os.rename(temp_filename, filename)


def drop_if_exists(filename: str) -> None:
    """Try deleting file before saving."""
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass


def create_folders_for_filename(path: Path, *segments: str) -> str:
    """Combine filename, create folders if they do not exist."""
    for i, segment in enumerate(segments, start=1):
        path /= segment

        if not path.exists() and i != len(segments):
            os.mkdir(path)

    return str(path.absolute())
