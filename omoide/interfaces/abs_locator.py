"""Interface for locator object."""

import abc
import functools

from omoide import domain


class AbsLocator(abc.ABC):
    """Abstract locator.

    Helps construct paths and urls to content/preview/thumbnail files.
    """

    def __init__(
        self,
        item: domain.Item,
        prefix_size: int,
    ) -> None:
        """Initialize instance."""
        self.item = item
        self.prefix_size = prefix_size

    @property
    @abc.abstractmethod
    def head(self) -> str:
        """Return starting common part of the path."""

    @property
    @abc.abstractmethod
    def body(self) -> str:
        """Return middle common part of the path."""

    @property
    @abc.abstractmethod
    def content(self) -> str:
        """Return path to the content."""

    @property
    @abc.abstractmethod
    def preview(self) -> str:
        """Return path to preview."""

    @property
    @abc.abstractmethod
    def thumbnail(self) -> str:
        """Return path to thumbnail."""

    @functools.cached_property
    def content_filename(self) -> str:
        """Return filename for the content."""
        if self.item.content_ext is None:
            return str(self.item.uuid)
        return f'{self.item.uuid}.{self.item.content_ext}'

    @functools.cached_property
    def preview_filename(self) -> str:
        """Return filename for the preview."""
        if self.item.preview_ext is None:
            return str(self.item.uuid)
        return f'{self.item.uuid}.{self.item.preview_ext}'

    @functools.cached_property
    def thumbnail_filename(self) -> str:
        """Return filename for the thumbnail."""
        if self.item.thumbnail_ext is None:
            return str(self.item.uuid)
        return f'{self.item.uuid}.{self.item.thumbnail_ext}'
