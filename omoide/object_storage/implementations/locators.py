"""Pathfinders."""

from omoide import models
from omoide.object_storage.interfaces.abs_locator import AbsLocator


class WebLocator(AbsLocator):
    """Web locator."""

    def __init__(self, root: str, prefix_size: int) -> None:
        """Initialize instance."""
        self.prefix_size = prefix_size
        self.root = root

    def get_content_location(self, item: models.Item) -> str | None:
        """Return location of the content."""
        prefix = str(item.uuid)[: self.prefix_size]
        ext = f'.{item.content_ext}' if item.content_ext else ''
        return f'/{self.root}/content/{item.owner_uuid}/{prefix}/{item.uuid}{ext}'

    def get_preview_location(self, item: models.Item) -> str | None:
        """Return location of the preview."""
        prefix = str(item.uuid)[: self.prefix_size]
        ext = f'.{item.preview_ext}' if item.preview_ext else ''
        return f'/{self.root}/preview/{item.owner_uuid}/{prefix}/{item.uuid}{ext}'

    def get_thumbnail_location(self, item: models.Item) -> str | None:
        """Return location of the thumbnail."""
        prefix = str(item.uuid)[: self.prefix_size]
        ext = f'.{item.thumbnail_ext}' if item.thumbnail_ext else ''
        return f'/{self.root}/thumbnail/{item.owner_uuid}/{prefix}/{item.uuid}{ext}'
