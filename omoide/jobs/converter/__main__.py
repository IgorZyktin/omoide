# -*- coding: utf-8 -*-
"""Converter job.

Transforms raw media into usable images,
extracts exif and does all the processing.
"""
import os

import click
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide.jobs.converter import database
from omoide.jobs.converter.conversion import convert_single_entry


@click.command()
@click.option('--limit', default=-1,
              help='Maximum amount of items to process')
def main(limit: int):
    """Converter entry point."""
    url = os.environ.get('OMOIDE_DB_URL')

    if url is None:
        raise ValueError('No database url supplied')

    engine = sqlalchemy.create_engine(url, echo=False)

    try:
        _convert(engine, limit)
    finally:
        engine.dispose()


def _convert(engine: Engine, limit: int) -> None:
    """Do actual job."""
    uuids = database.get_uuids_to_process(engine, limit)
    converted = 0

    for uuid in uuids:
        if database.claim(engine, uuid):
            with Session(engine) as session:
                raw_media = database.get_raw_media_instance(session, uuid)

                if raw_media is None:
                    print(f'Could not load raw media for {uuid}')
                    return

                try:
                    convert_single_entry(session, raw_media)
                except Exception as exc:
                    print(f'Failed to convert {uuid}: {exc}')
                else:
                    print(f'Converted {uuid}')
                    converted += 1
                finally:
                    session.commit()

    if converted:
        print(f'Conversion complete, total converted files: {converted}')


if __name__ == '__main__':
    main()
