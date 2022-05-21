# -*- coding: utf-8 -*-
"""Converter job.

Transforms raw media into usable images,
extracts exif and does all the processing.
"""
import os
from uuid import UUID

import click
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide.jobs.converter import database
from omoide.jobs.converter.conversion import convert_single_entry
from omoide.storage.database import models


@click.command()
@click.option('--limit',
              default=-1,
              help='Maximum amount of items to process')
@click.option('--batch',
              default=100,
              help='Handle this amount of items per request')
def main(limit: int, batch: int):
    """Converter entry point."""
    url = os.environ.get('OMOIDE_DB_URL')

    if url is None:
        raise ValueError('No database url supplied')

    engine = sqlalchemy.create_engine(url, echo=False)

    try:
        _convert(engine, limit, batch)
    finally:
        engine.dispose()


def _convert(engine: Engine, limit: int, batch: int) -> None:
    """Do actual job."""
    converted = 0
    handled = 0

    while True:
        if 0 < limit <= converted:
            break

        uuids = database.get_uuids_to_process(engine, batch)

        for uuid in uuids:
            if database.claim(engine, uuid):
                with Session(engine) as session:
                    raw_media = database.get_raw_media_instance(session, uuid)

                    if raw_media is None:
                        print(f'Could not load raw media for {uuid}')
                    else:
                        converted += _convert_single_media(
                            session, raw_media, handled + 1)

                    handled += 1

        if len(uuids) < batch:
            break

    if converted:
        delta = handled - converted
        if delta:
            print(f'Converted files: {converted} (and failed on {delta})')
        else:
            print(f'Converted files: {converted}')


_NAMES_CACHE: dict[UUID, str] = {}
_OWNERS_CACHE: dict[UUID, str] = {}


def _get_item_name(raw_media: models.RawMedia) -> str:
    """Get name for the item, preferable from cache."""
    name = _NAMES_CACHE.get(raw_media.item_uuid)

    if name is not None:
        return name

    name = raw_media.item.name
    _NAMES_CACHE[raw_media.item_uuid] = name
    return name


def _get_owner_name(raw_media: models.RawMedia) -> str:
    """Get owner name for the item, preferable from cache."""
    name = _OWNERS_CACHE.get(raw_media.item_uuid)

    if name is not None:
        return name

    name = raw_media.item.owner.name
    _OWNERS_CACHE[raw_media.item_uuid] = name
    return name


def _convert_single_media(
        session: Session,
        raw_media: models.RawMedia,
        number: int,
) -> int:
    """Convert one batch."""
    converted = 0
    item_name = _get_item_name(raw_media)
    owner_name = _get_owner_name(raw_media)
    try:
        convert_single_entry(session, raw_media)
    except Exception as exc:
        print(f'{number:04d}. Failed to convert {raw_media.item_uuid}: '
              f'{item_name} owned by {owner_name}, {exc}')
    else:
        print(f'{number:04d}. Converted {raw_media.item_uuid}, '
              f'{item_name} owned by {owner_name}')
        converted += 1
    finally:
        session.commit()

    return converted


if __name__ == '__main__':
    main()
