"""Pathfinders."""

from pathlib import Path
from typing import Literal
from uuid import UUID

from omoide import models
from omoide.object_storage.interfaces.abs_locator import AbsLocator


class FileLocator(AbsLocator):
    """Filesystem locator."""

    def __init__(self, data_folder: Path, prefix_size: int) -> None:
        """Initialize instance."""
        self.data_folder = data_folder
        self.prefix_size = prefix_size

    def get_content_location(self, item: models.Item) -> str | None:
        """Return location of the content."""
        if item.content_ext is None:
            return None
        return self._get_location(item.owner_uuid, item.uuid, 'content', item.content_ext)

    def get_preview_location(self, item: models.Item) -> str | None:
        """Return location of the preview."""
        if item.preview_ext is None:
            return None
        return self._get_location(item.owner_uuid, item.uuid, 'preview', item.content_ext)

    def get_thumbnail_location(self, item: models.Item) -> str | None:
        """Return location of the thumbnail."""
        if item.thumbnail_ext is None:
            return None
        return self._get_location(item.owner_uuid, item.uuid, 'thumbnail', item.content_ext)

    def _get_location(
        self,
        owner_uuid: UUID,
        item_uuid: UUID,
        category: Literal['content', 'preview', 'thumbnail'],
        ext: str,
    ) -> str:
        """Return generic location."""
        return str(
            self.data_folder
            / category
            / str(owner_uuid)
            / str(item_uuid)[: self.prefix_size]
            / f'{item_uuid}.{ext}'
        )


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
