# -*- coding: utf-8 -*-
"""Downloader job.

Transfers converted media onto local storage.
"""
import os
from pathlib import Path

import click
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import utils
from omoide.jobs.download import database
from omoide.jobs.download import download
from omoide.jobs.download import filesystem


@click.command()
@click.option('--limit', default=-1,
              help='Maximum amount of items to process')
@click.option('--strict/--no-strict', default=False,
              help='Raise exception in case of any problems')
def main(limit: int, strict: bool):
    """Converter entry point."""
    url = os.environ.get('OMOIDE_DB_URL')

    if url is None:
        raise ValueError('No database url supplied')

    folders = os.environ.get('OMOIDE_SAVE_TO_FOLDERS')

    if folders is None:
        raise ValueError('No folders to save given')

    paths = filesystem.extract_paths(folders)
    engine = sqlalchemy.create_engine(url, echo=False)

    try:
        _download(engine, paths, limit, strict)
    finally:
        engine.dispose()


def _download(
        engine: Engine,
        paths: list[Path],
        limit: int,
        strict: bool,
) -> None:
    """Do actual job."""
    with Session(engine) as session:
        media_records = database.get_media_records(session, limit)

        downloaded = 0
        for media in media_records:
            if database.claim(engine, media):
                try:
                    download.download_single_entry(media, paths)
                except Exception as exc:
                    if strict:
                        raise
                    else:
                        print(f'Failed to download {media.item_uuid}: {exc}')
                        media.status = 'fail'
                else:
                    print(f'Downloaded {media.item_uuid}')
                    media.status = 'done'
                    media.content = b''
                    downloaded += 1

                    if media.type == 'content':
                        media.item.content_ext = media.ext
                    elif media.type == 'preview':
                        media.item.preview_ext = media.ext
                    elif media.type == 'thumbnail':
                        media.item.thumbnail_ext = media.ext
                    else:
                        print(f'Unknown media type: {media.type!r}')

                finally:
                    media.processed_at = utils.now()
                    session.commit()

    if downloaded:
        print(f'Download complete, total downloaded files: {downloaded}')


if __name__ == '__main__':
    main()
