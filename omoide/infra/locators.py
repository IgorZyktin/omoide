"""Pathfinders."""

from pathlib import Path

from omoide import models


class BaseLocator:
    """Base pathfinder."""

    def __init__(self, prefix_size: int) -> None:
        """Initialize instance."""
        self.prefix_size = prefix_size

    def _get_prefix(self, item: models.Item) -> str:
        """Return prefix of the item."""
        return str(item.uuid)[: self.prefix_size]

    @staticmethod
    def _get_filename(item: models.Item, ext: str | None) -> str:
        """Return filename of the item."""
        return f'{item.uuid}.{ext}' if ext else ''


class WebLocator(BaseLocator):
    """Web locator."""

    def __init__(self, root: str, prefix_size: int) -> None:
        """Initialize instance."""
        super().__init__(prefix_size)
        self.root = root

    def get_video_location(self, item: models.Item) -> str | None:
        """Return location of the video."""
        if item.content_ext is None:
            return None

        prefix = str(item.uuid)[: self.prefix_size]
        ext = f'.{item.content_ext}' if item.content_ext else ''
        return f'/{self.root}/video/{item.owner_uuid}/{prefix}/{item.uuid}{ext}'

    def get_content_location(self, item: models.Item) -> str | None:
        """Return location of the content."""
        if item.content_ext is None:
            return None

        prefix = str(item.uuid)[: self.prefix_size]
        ext = f'.{item.content_ext}' if item.content_ext else ''
        return f'/{self.root}/content/{item.owner_uuid}/{prefix}/{item.uuid}{ext}'

    def get_preview_location(self, item: models.Item) -> str | None:
        """Return location of the preview."""
        if item.preview_ext is None:
            return None

        prefix = str(item.uuid)[: self.prefix_size]
        ext = f'.{item.preview_ext}' if item.preview_ext else ''
        return f'/{self.root}/preview/{item.owner_uuid}/{prefix}/{item.uuid}{ext}'

    def get_thumbnail_location(self, item: models.Item) -> str | None:
        """Return location of the thumbnail."""
        if item.thumbnail_ext is None:
            return None

        prefix = str(item.uuid)[: self.prefix_size]
        ext = f'.{item.thumbnail_ext}' if item.thumbnail_ext else ''
        return f'/{self.root}/thumbnail/{item.owner_uuid}/{prefix}/{item.uuid}{ext}'


class FilesystemLocator(BaseLocator):
    """Filesystem locator."""

    def __init__(self, root: Path, prefix_size: int) -> None:
        """Initialize instance."""
        super().__init__(prefix_size)
        self.root = root

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
            / 'video'
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
            / 'content'
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
            / 'preview'
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
            / 'thumbnail'
            / str(owner.uuid)
            / self._get_prefix(item)
            / self._get_filename(item, item.thumbnail_ext)
        )
