"""Object storage that saves data into files."""

import contextlib
from dataclasses import dataclass
from pathlib import Path

from omoide import models


@dataclass
class ImageSizes:
    """DTO for image size passing."""

    content_size: int | None = None
    preview_size: int | None = None
    thumbnail_size: int | None = None


class FileObjectStorageClient:
    """Object storage that saves data into files.

    This implementation is client-side. It works with the filesystem.
    """

    def __init__(self, folder: Path, prefix_size: int) -> None:
        """Initialize instance."""
        self.folder = folder
        self.prefix_size = prefix_size

    @staticmethod
    def _get_file_size(path: Path) -> int | None:
        """Return size in bytes for specific file."""
        with contextlib.suppress(FileNotFoundError):
            return path.stat().st_size
        return None

    def get_file_sizes(self, item: models.Item) -> ImageSizes:
        """Return image sizes for given item."""
        size = ImageSizes()

        if (content_path := self.get_content_path(item)) is not None:
            size.content_size = self._get_file_size(content_path)

        if (preview_path := self.get_preview_path(item)) is not None:
            size.preview_size = self._get_file_size(preview_path)

        if (thumbnail_path := self.get_thumbnail_path(item)) is not None:
            size.thumbnail_size = self._get_file_size(thumbnail_path)

        return size

    def get_content_path(self, item: models.Item) -> Path | None:
        """Return path co content."""
        if item.content_ext is None:
            return None
        return (
            self.folder
            / 'content'
            / str(item.owner_uuid)
            / str(item.uuid)[:self.prefix_size]
            / f'{item.uuid}.{item.content_ext}'
        )

    def get_preview_path(self, item: models.Item) -> Path | None:
        """Return path co content."""
        if item.preview_ext is None:
            return None
        return (
            self.folder
            / 'preview'
            / str(item.owner_uuid)
            / str(item.uuid)[:self.prefix_size]
            / f'{item.uuid}.{item.preview_ext}'
        )

    def get_thumbnail_path(self, item: models.Item) -> Path | None:
        """Return path co content."""
        if item.thumbnail_ext is None:
            return None
        return (
            self.folder
            / 'thumbnail'
            / str(item.owner_uuid)
            / str(item.uuid)[:self.prefix_size]
            / f'{item.uuid}.{item.thumbnail_ext}'
        )
