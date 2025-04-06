"""Object storage that works inside fastapi application."""

from omoide import models

# TODO: replace with data later
FOLDER = 'content'


class ObjectStorageWeb:
    """Object storage that works inside fastapi application."""

    def __init__(self, prefix_size: int):
        """Initialize instance."""
        self.prefix_size = prefix_size

    def get_content_url(self, item: models.Item) -> str:
        """Return URL to requested content type."""
        prefix = str(item.uuid)[: self.prefix_size]
        ext = f'.{item.content_ext}' if item.content_ext else ''
        return f'/{FOLDER}/content/{item.owner_uuid}/{prefix}/{item.uuid}{ext}'

    def get_preview_url(self, item: models.Item) -> str:
        """Return URL to requested content type."""
        prefix = str(item.uuid)[: self.prefix_size]
        ext = f'.{item.preview_ext}' if item.preview_ext else ''
        return f'/{FOLDER}/preview/{item.owner_uuid}/{prefix}/{item.uuid}{ext}'

    def get_thumbnail_url(self, item: models.Item) -> str:
        """Return URL to requested content type."""
        prefix = str(item.uuid)[: self.prefix_size]
        ext = f'.{item.thumbnail_ext}' if item.thumbnail_ext else ''
        return f'/{FOLDER}/thumbnail/{item.owner_uuid}/{prefix}/{item.uuid}{ext}'
