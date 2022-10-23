# -*- coding: utf-8 -*-
"""Thumbnail generation job.

Works only on collections, copies thumbnail of the first item as collection
thumbnail. Thumbnail propagation should be performed on the upload stage,
but if something gone wrong then, this job can fix that.
"""

import click
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import utils, jobs
from omoide.jobs.make_thumbnails import action


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
@click.option('--limit',
              default=-1,
              help='Maximum amount of items to process (-1 for infinity)')
def main(**kwargs):
    """Entry point."""
    config = jobs.JobConfig()
    jobs.apply_cli_kwargs_to_config(config, **kwargs)
    output = jobs.Output(silent=config.silent)

    output.print('Started <MAKE THUMBNAILS> job')
    output.print_config(config)

    with jobs.temporary_engine(config) as engine:
        use_thumbnail_of_first_as_collection_cover(config, engine, output)


MAXLEN_LOCATION = jobs.get_rest_of_the_terminal_width(
    jobs.MAXLEN_UUID,
    jobs.MAXLEN_UUID,
    max_width=jobs.TERMINAL_WIDTH,
)

COLUMNS = [
    jobs.MAXLEN_UUID,
    jobs.MAXLEN_UUID,
    jobs.MAXLEN_STATUS,
    MAXLEN_LOCATION,
]


def row_formatter(uuid_parent: str, uuid_child: str,
                  status: str, location: str) -> list[str]:
    """Construct one row for the table."""
    return [
        ' ' + uuid_parent.center(jobs.MAXLEN_UUID - 2) + ' ',
        ' ' + uuid_child.center(jobs.MAXLEN_UUID - 2) + ' ',
        ' ' + status.center(jobs.MAXLEN_STATUS - 2) + ' ',
        ' ' + location.ljust(MAXLEN_LOCATION - 2) + ' ',
    ]


def use_thumbnail_of_first_as_collection_cover(
        config: jobs.JobConfig,
        engine: Engine,
        output: jobs.Output,
) -> None:
    """Do the actual job."""
    copied = 0
    failed = 0
    start = utils.now()

    output.table_line(*COLUMNS)
    output.table_row(
        'UUID of the collection',
        'UUID of the first child',
        'Status',
        'Location',
        row_formatter=row_formatter,
    )
    output.table_line(*COLUMNS)

    with Session(engine) as session:
        last_seen = -1
        item = action.get_item_without_thumbnail(session, last_seen)

        while item is not None:
            last_seen = item.number  # type: ignore

            if 0 < config.limit <= copied:
                break

            first_child = action.get_first_child_with_thumbnail(session, item)

            if first_child is None:
                item = action.get_item_without_thumbnail(session, last_seen)
                continue

            location = jobs.database.get_cached_location_for_an_item(
                session=session,
                item_uuid=item.uuid,
            )

            try:
                done = action.copy_thumbnail(config, item, first_child)
            except Exception as exc:
                failed += 1
                if config.strict:
                    raise

                # TODO: replace it with proper logger call
                print(f'{type(exc).__name__}: {exc}')
            else:
                if done:
                    copied += 1
                    session.commit()
                    output.table_row(
                        str(item.uuid),
                        str(first_child.uuid),
                        'Copied',
                        utils.no_longer_than(location, MAXLEN_LOCATION - 2),
                        row_formatter=row_formatter,
                    )
                else:
                    failed += 1
                    output.table_row(
                        str(item.uuid),
                        str(first_child.uuid),
                        'Failed'.center(jobs.MAXLEN_STATUS, '!'),
                        utils.no_longer_than(location, MAXLEN_LOCATION - 2),
                        row_formatter=row_formatter,
                    )

            item = action.get_item_without_thumbnail(session, last_seen)

    output.table_line(*COLUMNS)

    if copied:
        output.print(f'Copied files: {utils.sep_digits(copied)}')

    if failed:
        output.print(f'Failed to copy: {utils.sep_digits(failed)}')

    stop = utils.now()
    duration = utils.human_readable_time(int((stop - start).total_seconds()))
    output.print(f'Time spent: {duration}')


if __name__ == '__main__':
    main()
