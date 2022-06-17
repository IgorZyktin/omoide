# -*- coding: utf-8 -*-
"""Download job.

By default, considers that database stores some
processed images which were put there by convert job.

We're using database as medium to transfer files from user to the server.
"""
from pathlib import Path

import click
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import utils
from omoide.jobs import common
from omoide.jobs.download import database
from omoide.jobs.download import download
from omoide.jobs.job_config import JobConfig


@click.command()
@click.option('--silent/--no-silent',
              default=False,
              help='Print output during work or just do it silently')
@click.option('--dry-run/--no-dry-run',
              default=True,
              help='Run script, but do not save changes')
@click.option('--batch-size',
              default=50,
              help='Process not more than this amount of objects at once')
@click.option('--limit',
              default=-1,
              help='Maximum amount of items to process (-1 for infinity)')
def main(**kwargs):
    """Entry point."""
    config = JobConfig()
    common.apply_cli_kwargs_to_config(config, **kwargs)

    with common.temporary_engine(config) as engine:
        _download(config, engine)


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
