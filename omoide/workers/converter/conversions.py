"""Media conversion operations."""

from collections.abc import Callable

from omoide import models
from omoide.workers.converter.cfg import WorkerConverterConfig
from omoide.workers.converter.interfaces import AbsStorage


def convert_static_image(
    config: WorkerConverterConfig,
    storage: AbsStorage,
    model: models.InputMedia,
) -> None:
    """Convert image (without animation)."""
    # TODO


CONVERTERS: dict[str, Callable] = {
    'image/png': convert_static_image,
    'image/jpeg': convert_static_image,
    'image/webp': convert_static_image,
}
