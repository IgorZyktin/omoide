"""Media conversion operations."""

import math
import tempfile
from collections.abc import Callable
from io import BytesIO
from typing import Final

from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
from moviepy import VideoFileClip

from omoide import const
from omoide import models
from omoide.workers.converter.cfg import WorkerConverterConfig
from omoide.workers.converter.database import ConverterPostgreSQLDatabase


def convert_static_image(
    config: WorkerConverterConfig,
    database: ConverterPostgreSQLDatabase,
    model: models.InputMedia,
) -> None:
    """Convert image (without animation)."""
    _ = config
    _convert_and_save_static_image_content(database, model)
    _convert_and_save_static_image_preview(database, model)
    _convert_and_save_static_image_thumbnail(database, model)


def convert_video(
    config: WorkerConverterConfig,
    database: ConverterPostgreSQLDatabase,
    model: models.InputMedia,
) -> None:
    """Convert video."""
    _ = config
    database.save_media(model, media_type='video')

    with tempfile.NamedTemporaryFile(suffix='.mp4') as temp_file:
        temp_file.write(model.content)
        with VideoFileClip(temp_file.name) as clip:
            first_frame = clip.get_frame(0)
            img = Image.fromarray(first_frame)

            old_width, old_height = img.size
            new_width, new_height = get_new_image_dimensions(
                old_width, old_height, const.PREVIEW_SIZE
            )
            preview = img.resize((new_width, new_height))
            preview = preview.convert('RGB')
            preview = preview.filter(ImageFilter.SHARPEN)

            buffer = BytesIO()
            preview.save(
                buffer,
                'JPEG',
                quality=const.IMAGE_QUALITY,
                optimize=True,
            )
            preview_data = buffer.getvalue()
            model.content = preview_data
            model.ext = 'jpg'
            model.content_type = 'image/jpeg'
            database.save_media(model, media_type='preview')

            new_width, new_height = get_new_image_dimensions(
                old_width, old_height, const.THUMBNAIL_SIZE
            )
            thumbnail = img.resize((new_width, new_height))
            thumbnail = thumbnail.convert('RGB')
            thumbnail = thumbnail.filter(ImageFilter.SHARPEN)

            buffer = BytesIO()
            thumbnail.save(
                buffer,
                'JPEG',
                quality=const.IMAGE_QUALITY,
                optimize=True,
            )
            thumbnail_data = buffer.getvalue()
            model.content = thumbnail_data
            model.ext = 'jpg'
            model.content_type = 'image/jpeg'
            database.save_media(model, media_type='thumbnail')


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
    database: ConverterPostgreSQLDatabase,
    model: models.InputMedia,
) -> None:
    """Save content."""
    database.save_media(model, media_type='content')


def _resize(content: bytes, size: int) -> bytes:
    """Resize to given dimensions."""
    stream = BytesIO(content)

    with Image.open(stream) as original_image:
        img = ImageOps.exif_transpose(original_image)
        old_width, old_height = img.size
        new_width, new_height = get_new_image_dimensions(
            old_width, old_height, size
        )
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
    database: ConverterPostgreSQLDatabase,
    model: models.InputMedia,
) -> None:
    """Save preview."""
    model.ext = 'jpg'
    model.content = _resize(model.content, const.PREVIEW_SIZE)
    database.save_media(model, media_type='preview')


def _convert_and_save_static_image_thumbnail(
    database: ConverterPostgreSQLDatabase,
    model: models.InputMedia,
) -> None:
    """Save thumbnail."""
    model.ext = 'jpg'
    model.content = _resize(model.content, const.THUMBNAIL_SIZE)
    database.save_media(model, media_type='thumbnail')


CONVERTERS: dict[str, Callable] = {
    const.CONTENT_TYPE_PNG: convert_static_image,
    const.CONTENT_TYPE_JPEG: convert_static_image,
    const.CONTENT_TYPE_WEBP: convert_static_image,
    const.CONTENT_TYPE_MP4: convert_video,
}

SUPPORTED_CONTENT_TYPES: Final = tuple(frozenset(CONVERTERS.keys()))
