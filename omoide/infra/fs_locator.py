"""Filesystem implementation for locator object."""

import functools
import os.path

from omoide import domain
from omoide import interfaces

__all__ = [
    'FilesystemLocator',
]


class FilesystemLocator(interfaces.AbsLocator):
    """Helper object that generates paths for files."""

    def __init__(
        self,
        base_folder: str,
        item: domain.Item,
        prefix_size: int,
    ) -> None:
        """Initialize instance."""
        super().__init__(item, prefix_size)
        self.base_folder = base_folder
        self.item = item
        self.prefix_size = prefix_size

    @functools.cached_property
    def head(self) -> str:
        """Return starting common part of the path."""
        return self.base_folder

    @functools.cached_property
    def body(self) -> str:
        """Return middle common part of the path."""
        return os.path.join(
            str(self.item.owner_uuid),
            str(self.item.uuid)[: self.prefix_size],
        )

    @functools.cached_property
    def content(self) -> str:
        """Return path to the content."""
        return os.path.join(
            self.head,
            'content',
            self.body,
            self.content_filename,
        )

    @functools.cached_property
    def preview(self) -> str:
        """Return path to the preview."""
        return os.path.join(
            self.head,
            'preview',
            self.body,
            self.preview_filename,
        )

    @functools.cached_property
    def thumbnail(self) -> str:
        """Return path to the thumbnail."""
        return os.path.join(
            self.head,
            'thumbnail',
            self.body,
            self.thumbnail_filename,
        )
