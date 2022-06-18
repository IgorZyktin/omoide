# -*- coding: utf-8 -*-
"""Download job.

By default, considers that database stores some
processed images which were put there by convert job.

We're using database as a medium to transfer files from user to the server.
"""
import click
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import jobs
from omoide import utils
from omoide.jobs.download import action
from omoide.storage.database import models


@click.command()
@click.option('--silent/--no-silent',
              default=False,
              help='Print output during work or just do it silently')
@click.option('--dry-run/--no-dry-run',
              default=True,
              help='Run script, but do not save changes')
@click.option('--strict/--no-strict',
              default=True,
              help='Stop processing on first error or try to complete all')
@click.option('--batch-size',
              default=50,
              help='Process not more than this amount of objects at once')
@click.option('--limit',
              default=-1,
              help='Maximum amount of items to process (-1 for infinity)')
def main(**kwargs):
    """Entry point."""
    config = jobs.JobConfig()
    jobs.apply_cli_kwargs_to_config(config, **kwargs)
    output = jobs.Output(silent=config.silent)

    output.print(f'Started <DOWNLOAD> job')
    output.print_config(config)

    with jobs.temporary_engine(config) as engine:
        download_items_from_database_to_storages(config, engine, output)


MAXLEN_LOCATION = jobs.get_rest_of_the_terminal_width(
    jobs.MAXLEN_UUID,
    jobs.MAXLEN_MEDIA_TYPE,
    jobs.MAXLEN_MEDIA_SIZE,
    jobs.MAXLEN_STATUS,
    max_width=jobs.TERMINAL_WIDTH,
)

COLUMNS = [
    jobs.MAXLEN_UUID,
    jobs.MAXLEN_MEDIA_TYPE,
    jobs.MAXLEN_MEDIA_SIZE,
    jobs.MAXLEN_STATUS,
    MAXLEN_LOCATION,
]


def row_formatter(uuid: str, media_type: str, media_size: str,
                  status: str, location: str) -> list[str]:
    """Construct one row for the table."""
    return [
        ' ' + uuid.center(jobs.MAXLEN_UUID - 2) + ' ',
        ' ' + media_type.center(jobs.MAXLEN_MEDIA_TYPE - 2) + ' ',
        ' ' + media_size.center(jobs.MAXLEN_MEDIA_SIZE - 2) + ' ',
        ' ' + status.center(jobs.MAXLEN_STATUS - 2) + ' ',
        ' ' + location.ljust(MAXLEN_LOCATION - 2) + ' ',
    ]


def download_items_from_database_to_storages(
        config: jobs.JobConfig,
        engine: Engine,
        output: jobs.Output,
) -> None:
    """Do the actual job."""
    downloaded = 0
    failed = 0
    start = utils.now()

    output.table_line(*COLUMNS)
    output.table_row('UUID', 'Type', 'Size', 'Status', 'Location',
                     row_formatter=row_formatter)
    output.table_line(*COLUMNS)

    for batch in jobs.database.get_candidates(config, engine, action.get_media):
        for media_id in batch:
            if config.dry_run or \
                    jobs.database.claim(engine, media_id, models.Media):

                with Session(engine) as session:
                    media = session.query(models.Media).get(media_id)
                    size = -1

                    if media is None:
                        # TODO: replace it with proper logger call
                        print(f'Media {media_id} disappeared before download!')
                        continue

                    try:
                        size = len(media.content)
                        result = action.process_single_media(config, media)

                    except Exception as exc:
                        result = 'exc'

                        if config.strict:
                            raise

                        # TODO: replace it with proper logger call
                        print(f'{type(exc).__name__}: {exc}')

                    if not config.dry_run:
                        action.finalize_media(session, media, result)

                    if result == 'ok':
                        status = 'done'
                        downloaded += 1
                    else:
                        status = 'failed'
                        failed += 1

                    location = jobs.database.get_cached_location_for_an_item(
                        session=session,
                        item_uuid=media.item_uuid,
                    )

                    output.table_row(
                        str(media.item_uuid),
                        str(media.type),
                        utils.byte_count_to_text(size),
                        status,
                        utils.no_longer_than(location, MAXLEN_LOCATION - 2),
                        row_formatter=row_formatter,
                    )

    output.table_line(*COLUMNS)

    if downloaded:
        output.print(f'Downloaded files: {utils.sep_digits(downloaded)}')

    if failed:
        output.print(f'Failed to download: {utils.sep_digits(failed)}')

    stop = utils.now()
    duration = utils.human_readable_time(int((stop - start).total_seconds()))
    output.print(f'Time spent: {duration}')


if __name__ == '__main__':
    main()
