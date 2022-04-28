# -*- coding: utf-8 -*-
"""Converter implementation.
"""
from typing import Optional

from sqlalchemy.orm import Session

from omoide import utils
from omoide.jobs.converter import features
from omoide.jobs.converter import renderer
from omoide.storage.database.models import Meta, RawMedia

VALID_EXT = frozenset([
    'jpg',
])


def convert_single_entry(session: Session, raw_media: RawMedia) -> None:
    """Perform full conversion for single entry."""
    ext = extract_ext(raw_media.filename)

    if not ext or ext not in VALID_EXT:
        print(f'Cant handle {raw_media.item_uuid}, filename '
              f'has unsupported ext: {raw_media.filename!r}')
        return

    if not raw_media.content:
        print(f'Nothing to convert for {raw_media.item_uuid}')
        return

    item = raw_media.item

    if item.meta is None:
        meta = Meta(item_uuid=item.uuid, data={})
        session.add(meta)
        session.commit()

    image = renderer.get_image(raw_media)
    size = len(raw_media.content or '')
    renderer.gather_media_parameters(item, image, size)

    features.apply_features(item, image)
    content = renderer.save_content(item, image, ext)
    preview = renderer.save_preview(item, image, ext)
    thumbnail = renderer.save_thumbnail(item, image, ext)
    session.add_all([content, preview, thumbnail])

    raw_media.status = 'done'
    raw_media.processed_at = utils.now()
    raw_media.content = b''
    image.close()


def extract_ext(filename: Optional[str]) -> str:
    """Extract filename from extension.

    >>> extract_ext('test.txt')
    'txt'

    >>> extract_ext('test')
    ''

    >>> extract_ext('test.txt.bak')
    'bak'
    """
    if not filename:
        return ''

    parts = filename.rsplit('.', maxsplit=1)
    if len(parts) == 1:
        return ''

    return parts[-1].lower()
