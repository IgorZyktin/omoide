"""Media conversion operations."""

import math
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

    if not model.extras.get('skip_content'):
        _convert_and_save_static_image_content(database, model)

    stream = BytesIO(model.content)
    with Image.open(stream) as img:
        if not model.extras.get('skip_preview'):
            _convert_and_save_static_image_preview(database, model, img)
        _convert_and_save_static_image_thumbnail(database, model, img)


def convert_video(
    config: WorkerConverterConfig,
    database: ConverterPostgreSQLDatabase,
    model: models.InputMedia,
) -> None:
    """Convert video."""
    if not model.extras.get('skip_content'):
        _conver_and_save_video_content(database, model)

    tmp_path = config.temp_folder / f'{model.item_uuid}.{model.ext}'

    try:
        with open(tmp_path, mode='wb') as file:
            file.write(model.content)
            try:
                clip = VideoFileClip(tmp_path)
                first_frame = clip.get_frame(0)
                img = Image.fromarray(first_frame)

                if not model.extras.get('skip_preview'):
                    _convert_and_save_static_image_preview(
                        database, model, img
                    )
                _convert_and_save_static_image_thumbnail(database, model, img)
            finally:
                clip.close()
    finally:
        tmp_path.unlink(missing_ok=True)


def _conver_and_save_video_content(
    database: ConverterPostgreSQLDatabase,
    model: models.InputMedia,
) -> None:
    """Save content."""
    database.save_output_media(model, media_type='video')


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
    database.save_output_media(model, media_type='content')


def _resize(img: Image.Image, size: int) -> bytes:
    """Resize to given dimensions."""
    img = ImageOps.exif_transpose(img)
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
    img: Image.Image,
) -> None:
    """Save preview."""
    new_model = models.InputMedia(
        id=1,
        user_uuid=model.user_uuid,
        item_uuid=model.item_uuid,
        created_at=model.created_at,
        ext='jpg',
        content_type='image/jpeg',
        extras=model.extras,
        error=model.error,
        content=_resize(img, const.PREVIEW_SIZE),
    )
    database.save_output_media(new_model, media_type='preview')


def _convert_and_save_static_image_thumbnail(
    database: ConverterPostgreSQLDatabase,
    model: models.InputMedia,
    img: Image.Image,
) -> None:
    """Save thumbnail."""
    new_model = models.InputMedia(
        id=1,
        user_uuid=model.user_uuid,
        item_uuid=model.item_uuid,
        created_at=model.created_at,
        ext='jpg',
        content_type='image/jpeg',
        extras=model.extras,
        error=model.error,
        content=_resize(img, const.THUMBNAIL_SIZE),
    )
    database.save_output_media(new_model, media_type='thumbnail')


CONVERTERS: dict[str, Callable] = {
    const.CONTENT_TYPE_PNG: convert_static_image,
    const.CONTENT_TYPE_JPEG: convert_static_image,
    const.CONTENT_TYPE_WEBP: convert_static_image,
    const.CONTENT_TYPE_MP4: convert_video,
    const.CONTENT_TYPE_WEBM: convert_video,
}

SUPPORTED_CONTENT_TYPES: Final = tuple(frozenset(CONVERTERS.keys()))
