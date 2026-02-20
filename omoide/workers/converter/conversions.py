"""Media conversion operations."""

from collections.abc import Callable
from io import BytesIO
import math
from typing import Final

from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps

from omoide import const
from omoide import models
from omoide.workers.converter.cfg import WorkerConverterConfig
from omoide.workers.converter.interfaces import AbsDatabase


def convert_static_image(
    config: WorkerConverterConfig,
    database: AbsDatabase,
    model: models.InputMedia,
) -> None:
    """Convert image (without animation)."""
    _ = config
    _convert_and_save_static_image_content(database, model)
    _convert_and_save_static_image_preview(database, model)
    _convert_and_save_static_image_thumbnail(database, model)


def get_new_image_dimensions(
    old_width: int,
    old_height: int,
    new_size: int,
) -> tuple[int, int]:
    """Calculate new size while maintaining proportions."""
    if old_width >= old_height:
        new_width = float(min(old_width, new_size))
        coefficient = new_width / old_width
        new_height = old_height * coefficient
    else:
        new_height = min(old_height, new_size)
        coefficient = new_height / old_height
        new_width = old_width * coefficient

    return math.ceil(new_width), math.ceil(new_height)


def _convert_and_save_static_image_content(
    database: AbsDatabase,
    model: models.InputMedia,
) -> None:
    """Save content."""
    database.save_media(model, media_type='content')


def _resize(model: models.InputMedia, size: int) -> bytes:
    """Resize to given dimensions."""
    stream = BytesIO(model.content)

    with Image.open(stream) as original_image:
        img = ImageOps.exif_transpose(original_image)
        old_width, old_height = img.size
        new_width, new_height = get_new_image_dimensions(old_width, old_height, size)
        new_img = img.resize((new_width, new_height))
        new_img = new_img.convert('RGB')
        new_img = new_img.filter(ImageFilter.SHARPEN)

        buffer = BytesIO()
        new_img.save(
            buffer,
            'JPEG',
            quality=const.IMAGE_QUALITY,
            optimize=True,
        )
        new_payload = buffer.getvalue()

    return new_payload


def _convert_and_save_static_image_preview(
    database: AbsDatabase,
    model: models.InputMedia,
) -> None:
    """Save preview."""
    model.ext = 'jpg'
    model.content = _resize(model, const.PREVIEW_SIZE)
    database.save_media(model, media_type='preview')


def _convert_and_save_static_image_thumbnail(
    database: AbsDatabase,
    model: models.InputMedia,
) -> None:
    """Save thumbnail."""
    model.ext = 'jpg'
    model.content = _resize(model, const.THUMBNAIL_SIZE)
    database.save_media(model, media_type='thumbnail')


CONVERTERS: dict[str, Callable] = {
    const.CONTENT_TYPE_PNG: convert_static_image,
    const.CONTENT_TYPE_JPEG: convert_static_image,
    const.CONTENT_TYPE_WEBP: convert_static_image,
}

SUPPORTED_CONTENT_TYPES: Final = tuple(frozenset(CONVERTERS.keys()))
