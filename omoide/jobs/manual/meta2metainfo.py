# -*- coding: utf-8 -*-
"""Manual script that converts old meta records to new metainfo records."""
from datetime import datetime

import click
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import jobs
from omoide import utils
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
@click.option('--limit',
              default=10000,
              help='Maximum amount of items to process (-1 for infinity)')
def main(**kwargs):
    """Entry point."""
    config = jobs.JobConfig()
    jobs.apply_cli_kwargs_to_config(config, **kwargs)

    with jobs.temporary_engine(config) as engine:
        convert_meta_records_to_metainfo_records(config, engine)


def convert_meta_records_to_metainfo_records(
        config: jobs.JobConfig,
        engine: Engine,
) -> None:
    """Do the actual job."""
    print('Saving meta records as metainfo records')
    start = utils.now()

    with Session(engine) as session:
        metas = session.query(
            models.Meta
        ).order_by(
            models.Meta.item_uuid
        ).limit(
            config.limit
        )

        for meta in metas:
            metainfo = session.query(models.Metainfo).get(meta.item_uuid)
            if metainfo is None:
                now = utils.now()
                metainfo = models.Metainfo(
                    item_uuid=meta.item_uuid,
                    created_at=now,
                    updated_at=now,
                    extras={},
                )
                session.add(metainfo)
            copied_all = cast_meta_to_metainfo(meta, metainfo)
            if copied_all:
                # print(f'Saving {meta.item_uuid}')
                session.delete(meta)
            else:
                print(f'---> Skipping {meta.item_uuid}')
            session.commit()

    stop = utils.now()
    duration = utils.human_readable_time(int((stop - start).total_seconds()))
    print(f'Time spent: {duration}')


def parse_time(string: str) -> datetime:
    """Safely parse time."""
    try:
        dt = datetime.strptime(string, '%Y-%m-%d %H:%M:%S.%f%z')
    except ValueError:
        dt = datetime.strptime(string, '%Y-%m-%d %H:%M:%S%z')
    return dt


def cast_meta_to_metainfo(
        meta: models.Meta,
        metainfo: models.Metainfo,
) -> bool:
    """Copy and convert parameters.

    Return True if copied everything.
    """
    for key, value in tuple(meta.data.items()):
        found = True
        if key == 'res':
            metainfo.resolution = value
        elif key == 'size':
            metainfo.size = value
        elif key == 'width':
            metainfo.width = value
        elif key == 'height':
            metainfo.height = value
        elif key == 'type':
            metainfo.media_type = value
        elif key == 'original_file_name':
            metainfo.extras['original_file_name'] = value
        elif key == 'original_file_modified_at':
            metainfo.extras['original_file_modified_at'] = value
        elif key == 'registered_on':
            dt = parse_time(value)
            metainfo.created_at = dt
            metainfo.updated_at = utils.now()
        elif key == 'origin_url':
            metainfo.saved_from_url = value
        elif key == 'author':
            metainfo.author = value
        elif key == 'author_url':
            metainfo.author_url = value
        else:
            found = False
            print('\t', key, repr(value))

        if found:
            del meta.data[key]

    return not bool(meta.data)


if __name__ == '__main__':
    main()
