# -*- coding: utf-8 -*-
"""Converter implementation.
"""
import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from omoide.jobs.converter import database
from omoide.jobs.converter import features
from omoide.jobs.converter import renderer
from omoide.storage.database.models import Meta

VALID_EXT = frozenset([
    'jpg',
])


def convert_single_entry(session: Session, uuid: UUID) -> None:
    """Perform full conversion for single entry."""
    raw_media = database.get_raw_media_instance(session, uuid)

    if raw_media is None:
        print(f'Could not load raw media for {uuid}')
        return

    ext = extract_ext(raw_media.filename)

    if not ext or ext not in VALID_EXT:
        print(f'Cant handle {uuid}, filename '
              f'has unsupported ext: {raw_media.filename!r}')
        return

    item = raw_media.item

    if item.meta is None:
        meta = Meta(item_uuid=item.uuid, data={})
        session.add(meta)
        session.commit()

    image = renderer.get_image(raw_media)
    renderer.gather_media_parameters(item, image, len(raw_media.content))

    features.apply_features(item, image)
    content = renderer.save_content(item, image, ext)
    preview = renderer.save_preview(item, image, ext)
    thumbnail = renderer.save_thumbnail(item, image, ext)
    session.add_all([content, preview, thumbnail])

    raw_media.status = 'done'
    raw_media.processed_at = datetime.datetime.now(tz=datetime.timezone.utc)
    raw_media.content = b''
    image.close()


def extract_ext(filename: str) -> str:
    """Extract filename from extension.

    >>> extract_ext('test.txt')
    'txt'

    >>> extract_ext('test')
    ''

    >>> extract_ext('test.txt.bak')
    'bak'
    """
    parts = filename.rsplit('.', maxsplit=1)
    if len(parts) == 1:
        return ''
    return parts[-1].lower()
