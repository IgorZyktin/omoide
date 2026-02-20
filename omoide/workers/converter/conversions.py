"""Media conversion operations."""
import math
from collections.abc import Callable
from PIL import ExifTags
from PIL import Image
from io import BytesIO
from PIL import ImageFilter
from PIL import ImageOps

from omoide import const
from omoide import models
from omoide.workers.converter.cfg import WorkerConverterConfig
from omoide.workers.converter.interfaces import AbsStorage


def convert_static_image(
    config: WorkerConverterConfig,
    storage: AbsStorage,
    model: models.InputMedia,
) -> None:
    """Convert image (without animation)."""
    _convert_and_save_static_image_content(config, storage, model)
    _convert_and_save_static_image_preview(config, storage, model)
    _convert_and_save_static_image_thumbnail(config, storage, model)


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
    config: WorkerConverterConfig,
    storage: AbsStorage,
    model: models.InputMedia,
) -> None:
    """Save content."""
    _ = config
    storage.save_model(model, media_type='content')


def _convert_and_save_static_image_preview(
    config: WorkerConverterConfig,
    storage: AbsStorage,
    model: models.InputMedia,
) -> None:
    """Save preview."""
    _ = config
    stream = BytesIO(model.content)

    with Image.open(stream) as original_image:
        img = ImageOps.exif_transpose(original_image)
        old_width, old_height = img.size
        new_width, new_height = get_new_image_dimensions(
            old_width, old_height, const.THUMBNAIL_SIZE
        )
        new_img = img.resize((new_width, new_height))
        new_img = new_img.convert('RGB')
        new_img = new_img.filter(ImageFilter.SHARPEN)

        buffer = BytesIO()
        new_img.save(buffer, 'JPEG', quality=const.IMAGE_QUALITY, optimize=True)
        new_payload = buffer.getvalue()
        model.content = new_payload

    storage.save_model(model, media_type='preview')


def _convert_and_save_static_image_thumbnail(
    config: WorkerConverterConfig,
    storage: AbsStorage,
    model: models.InputMedia,
) -> None:
    """Save thumbnail."""
    _ = config
    storage.save_model(model, media_type='thumbnail')


CONVERTERS: dict[str, Callable] = {
    'image/png': convert_static_image,
    'image/jpeg': convert_static_image,
    'image/webp': convert_static_image,
}
