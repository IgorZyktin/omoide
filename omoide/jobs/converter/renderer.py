# -*- coding: utf-8 -*-
"""Actual media manipulations.
"""
import datetime
import io
import math

from PIL import Image
from sqlalchemy.orm.attributes import flag_modified

from omoide.domain import RawMedia
from omoide.storage.database.models import Item, Media


def get_image(raw_media: RawMedia) -> Image:
    """Extract binary data from raw media."""
    return Image.open(io.BytesIO(raw_media.content))


def gather_media_parameters(item: Item, image: Image, size: int) -> None:
    """Extract basic parameters from the item."""
    width, height = image.size

    item.meta.data.update({
        'width': width,
        'height': height,
        'res': round(width * height / 1_000_000, 2),
        'size': size,
        'type': 'image',
        'registered_on': str(datetime.datetime.now(tz=datetime.timezone.utc)),
    })
    flag_modified(item.meta, 'data')


def calculate_size(
        original_width: int,
        original_height: int,
        target_width: int,
        target_height: int
) -> tuple[int, int]:
    """Return dimensions for resized variant.

    Unlike pillow, this method revolves around height.
    We have strict target height but can tolerate various
    variants of width.
    """
    if not all([
        original_width,
        original_height,
        target_width,
        target_height,
    ]):
        raise ValueError('Cannot resize to zero')

    dimension = min(target_height, original_height)
    coefficient = dimension / original_height
    resulting_width = math.ceil(coefficient * original_width)
    return resulting_width, dimension


def image_to_bytes(image: Image, **kwargs) -> bytes:
    """Convert image into raw bytes."""
    storage = io.BytesIO()
    # TODO - add more formats
    image.save(storage, format='JPEG', **kwargs)
    return storage.getvalue()


def save_content(item: Item, image: Image, ext: str) -> Media:
    """Save content of the item."""
    return Media(
        item_uuid=item.uuid,
        created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        processed_at=None,
        status='init',
        type='content',
        ext=ext,
        content=image_to_bytes(image),
    )


def save_preview(item: Item, image: Image, ext: str) -> Media:
    """Save medium representation of the item."""
    return _save_downscaled(
        item=item,
        image=image,
        ext=ext,
        target_type='preview',
        target_width=1024,
        target_height=1024,
    )


def save_thumbnail(item: Item, image: Image, ext: str) -> Media:
    """Save smallest representation of the item."""
    return _save_downscaled(
        item=item,
        image=image,
        ext=ext,
        target_type='thumbnail',
        target_width=384,
        target_height=384,
    )


def _save_downscaled(
        item: Item,
        image: Image,
        ext: str,
        target_type: str,
        target_width: int,
        target_height: int,
) -> Media:
    """Common downscale function."""
    if ext != 'jpg':
        image = image.convert('RGB')

    # TODO - these parameters are only for jpg
    kwargs = {
        'quality': 80,
        'progressive': True,
        'optimize': True,
        'subsampling': 0,
    }

    width, height = calculate_size(
        original_width=image.width,
        original_height=image.height,
        target_width=target_width,
        target_height=target_height,
    )
    smaller_image = image.resize((width, height))

    return Media(
        item_uuid=item.uuid,
        created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        processed_at=None,
        status='init',
        type=target_type,
        ext='jpg',
        content=image_to_bytes(smaller_image, **kwargs),
    )
