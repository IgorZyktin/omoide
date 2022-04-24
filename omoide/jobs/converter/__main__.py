# -*- coding: utf-8 -*-
"""Converter job.

Transforms raw media into usable images,
extracts exif and does all the processing.
"""
import os

import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide.jobs.converter import database
from omoide.jobs.converter.conversion import convert_single_entry


def main():
    """Converter entry point."""
    url = os.environ.get('OMOIDE_DB_URL')

    if url is None:
        raise ValueError('No database url supplied')

    engine = sqlalchemy.create_engine(url, echo=False)

    try:
        _convert(engine)
    finally:
        engine.dispose()


def _convert(engine: Engine) -> None:
    """Do actual job."""
    uuids = database.get_uuids_to_process(engine, limit=100)
    converted = 0

    for uuid in uuids:
        if database.claim(engine, uuid):
            with Session(engine) as session:
                convert_single_entry(session, uuid)
                session.commit()
                print(f'Converted {uuid}')
                converted += 1

    print(f'Conversion complete, total converted files: {converted}')


if __name__ == '__main__':
    main()
