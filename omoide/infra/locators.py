"""Pathfinders."""

from pathlib import Path

from omoide import const
from omoide import models


class LocatorMixin:
    """Generic pathfinder operations."""

    prefix_size: int

    def _get_prefix(self, item: models.Item) -> str:
        """Return prefix of the item."""
        return str(item.uuid)[: self.prefix_size]

    @staticmethod
    def _get_filename(item: models.Item, ext: str | None) -> str:
        """Return filename of the item."""
        return f'{item.uuid}.{ext}' if ext else ''


class WebLocator(LocatorMixin):
    """Web locator."""

    def __init__(self, root: str, prefix_size: int) -> None:
        """Initialize instance."""
        self.root = root
        self.prefix_size = prefix_size

    def get_video_location(self, item: models.Item) -> str | None:
        """Return location of the video."""
        if item.content_ext is None:
            return None

        return (
            f'/{self.root}'
            f'/{const.MediaType.VIDEO}'
            f'/{item.owner_uuid}'  # FIXME - do not use `owner_uuid` attribute
            f'/{self._get_prefix(item)}'
            f'/{self._get_filename(item, item.content_ext)}'
        )

    def get_content_location(self, item: models.Item) -> str | None:
        """Return location of the content."""
        if item.content_ext is None:
            return None

        return (
            f'/{self.root}'
            f'/{const.MediaType.CONTENT}'
            f'/{item.owner_uuid}'  # FIXME - do not use `owner_uuid` attribute
            f'/{self._get_prefix(item)}'
            f'/{self._get_filename(item, item.content_ext)}'
        )

    def get_preview_location(self, item: models.Item) -> str | None:
        """Return location of the preview."""
        if item.preview_ext is None:
            return None

        return (
            f'/{self.root}'
            f'/{const.MediaType.PREVIEW}'
            f'/{item.owner_uuid}'  # FIXME - do not use `owner_uuid` attribute
            f'/{self._get_prefix(item)}'
            f'/{self._get_filename(item, item.preview_ext)}'
        )

    def get_thumbnail_location(self, item: models.Item) -> str | None:
        """Return location of the thumbnail."""
        if item.thumbnail_ext is None:
            return None

        return (
            f'/{self.root}'
            f'/{const.MediaType.THUMBNAIL}'
            f'/{item.owner_uuid}'  # FIXME - do not use `owner_uuid` attribute
            f'/{self._get_prefix(item)}'
            f'/{self._get_filename(item, item.thumbnail_ext)}'
        )


class FilesystemLocator(LocatorMixin):
    """Filesystem locator."""

    def __init__(self, root: Path, prefix_size: int) -> None:
        """Initialize instance."""
        self.root = root
        self.prefix_size = prefix_size

    def get_video_location(
        self,
        owner: models.User,
        item: models.Item,
    ) -> Path | None:
        """Return location of the video."""
        if item.content_ext is None:
            return None

        return (
            self.root
            / const.MediaType.VIDEO
            / str(owner.uuid)
            / self._get_prefix(item)
            / self._get_filename(item, item.content_ext)
        )

    def get_content_location(
        self,
        owner: models.User,
        item: models.Item,
    ) -> Path | None:
        """Return location of the content."""
        if item.content_ext is None:
            return None

        return (
            self.root
            / const.MediaType.CONTENT
            / str(owner.uuid)
            / self._get_prefix(item)
            / self._get_filename(item, item.content_ext)
        )

    def get_preview_location(
        self,
        owner: models.User,
        item: models.Item,
    ) -> Path | None:
        """Return location of the preview."""
        if item.preview_ext is None:
            return None

        return (
            self.root
            / const.MediaType.PREVIEW
            / str(owner.uuid)
            / self._get_prefix(item)
            / self._get_filename(item, item.preview_ext)
        )

    def get_thumbnail_location(
        self,
        owner: models.User,
        item: models.Item,
    ) -> Path | None:
        """Return location of the thumbnail."""
        if item.thumbnail_ext is None:
            return None

        return (
            self.root
            / const.MediaType.THUMBNAIL
            / str(owner.uuid)
            / self._get_prefix(item)
            / self._get_filename(item, item.thumbnail_ext)
        )
