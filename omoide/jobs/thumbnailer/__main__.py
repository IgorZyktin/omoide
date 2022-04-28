# -*- coding: utf-8 -*-
"""Thumbnail generation job.

Works only on collections, copies thumbnail of
the first item as collection thumbnail.
"""
import os
import random
import shutil
from pathlib import Path

import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import utils
from omoide.jobs.downloader import filesystem
from omoide.jobs.thumbnailer import database
from omoide.storage.database.models import Item


def main():
    """Thumbnailer entry point."""
    url = os.environ.get('OMOIDE_DB_URL')

    if url is None:
        raise ValueError('No database url supplied')

    folders = os.environ.get('OMOIDE_SAVE_TO_FOLDERS')

    if folders is None:
        raise ValueError('No folders to save given')

    paths = filesystem.extract_paths(folders)
    engine = sqlalchemy.create_engine(url, echo=False)

    try:
        _copy_thumbnails(engine, paths)
    finally:
        engine.dispose()


def _copy_thumbnails(engine: Engine, paths: list[Path]) -> None:
    """Do actual job."""
    with Session(engine) as session:
        items = database.get_items_without_thumbnail(session)

        for item in items:
            first_child = database.get_first_child(session, item)

            if first_child is None:
                continue

            done = copy_single_thumbnail(first_child, item, paths)

            if done:
                print(f'Copied {first_child.uuid} -> {item.uuid}')
                session.commit()


def copy_single_thumbnail(
        source: Item,
        target: Item,
        paths: list[Path],
) -> bool:
    """Perform thumbnail copy for single entry, return True on success."""
    for path in paths:
        if not source.thumbnail_ext:
            return False

        target.thumbnail_ext = source.thumbnail_ext

        source_bucket = utils.get_bucket(source.uuid)
        target_bucket = utils.get_bucket(target.uuid)

        source_filename = filesystem.create_folders_for_filename(
            path,
            str(source.owner_uuid),
            'thumbnail',
            source_bucket,
            f'{source.uuid}.{source.thumbnail_ext}'
        )

        target_filename = filesystem.create_folders_for_filename(
            path,
            str(target.owner_uuid),
            'thumbnail',
            target_bucket,
            f'{target.uuid}.{target.thumbnail_ext}'
        )

        temp_filename = source_filename + '.tmp' + str(random.randint(1, 1000))

        filesystem.drop_if_exists(target_filename)
        filesystem.drop_if_exists(temp_filename)

        shutil.copyfile(source_filename, temp_filename)
        os.rename(temp_filename, target_filename)

    return True


if __name__ == '__main__':
    main()
