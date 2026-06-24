"""Pathfinders."""

from pathlib import Path
from typing import assert_never

from omoide import const
from omoide import models


class LocatorMixin:
    """Generic pathfinder operations."""

    prefix_size: int

    def get_prefix(self, item: models.Item) -> str:
        """Return prefix of the item."""
        return str(item.uuid)[: self.prefix_size]

    @staticmethod
    def get_filename(
        item: models.Item,
        ext: str | None,
        *,
        deleted: bool = False,
    ) -> str:
        """Return filename of the item."""
        filename = str(item.uuid)

        if ext is not None:
            filename = f'{filename}.{ext}'

        if deleted:
            return f'deleted___{filename}'

        return filename


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
            f'/{self.get_prefix(item)}'
            f'/{self.get_filename(item, item.content_ext)}'
        )

    def get_content_location(self, item: models.Item) -> str | None:
        """Return location of the content."""
        if item.content_ext is None:
            return None

        return (
            f'/{self.root}'
            f'/{const.MediaType.CONTENT}'
            f'/{item.owner_uuid}'  # FIXME - do not use `owner_uuid` attribute
            f'/{self.get_prefix(item)}'
            f'/{self.get_filename(item, item.content_ext)}'
        )

    def get_preview_location(self, item: models.Item) -> str | None:
        """Return location of the preview."""
        if item.preview_ext is None:
            return None

        return (
            f'/{self.root}'
            f'/{const.MediaType.PREVIEW}'
            f'/{item.owner_uuid}'  # FIXME - do not use `owner_uuid` attribute
            f'/{self.get_prefix(item)}'
            f'/{self.get_filename(item, item.preview_ext)}'
        )

    def get_thumbnail_location(self, item: models.Item) -> str | None:
        """Return location of the thumbnail."""
        if item.thumbnail_ext is None:
            return None

        return (
            f'/{self.root}'
            f'/{const.MediaType.THUMBNAIL}'
            f'/{item.owner_uuid}'  # FIXME - do not use `owner_uuid` attribute
            f'/{self.get_prefix(item)}'
            f'/{self.get_filename(item, item.thumbnail_ext)}'
        )


class FilesystemLocator(LocatorMixin):
    """Filesystem locator."""

    def __init__(self, root: Path, prefix_size: int) -> None:
        """Initialize instance."""
        self.root = root
        self.prefix_size = prefix_size

    def get_path_segments(
        self,
        owner: models.User,
        item: models.Item,
        media_type: const.MediaType,
        *,
        deleted: bool = False,
        force_ext: str | None = None,
    ) -> tuple[Path, const.MediaType, str, str, str] | None:
        """Return all path components separately."""
        ext: str | None

        if force_ext is not None:
            ext = force_ext
        else:
            match media_type:
                case media_type.VIDEO:
                    ext = item.content_ext
                case media_type.CONTENT:
                    ext = item.content_ext
                case media_type.PREVIEW:
                    ext = item.preview_ext
                case media_type.THUMBNAIL:
                    ext = item.thumbnail_ext
                case _:
                    assert_never(media_type)
                    raise  # noqa: PLE0704

        if ext is None:
            return None

        return (
            self.root,
            media_type,
            str(owner.uuid),
            self.get_prefix(item),
            self.get_filename(item, ext, deleted=deleted),
        )

    def get_path(
        self,
        owner: models.User,
        item: models.Item,
        media_type: const.MediaType,
        *,
        deleted: bool = False,
        force_ext: str | None = None,
    ) -> Path | None:
        """Get path to the file."""
        segments = self.get_path_segments(
            owner,
            item,
            media_type,
            deleted=deleted,
            force_ext=force_ext,
        )

        if segments is None:
            return None

        _root, _media, _uuid, _prefix, _filename = segments
        return _root / _media / _uuid / _prefix / _filename
