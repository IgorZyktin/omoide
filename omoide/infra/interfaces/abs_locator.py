"""Abstract base pathfinder."""

import abc

from omoide import models


class AbsLocator(abc.ABC):
    """Abstract base pathfinder."""

    @abc.abstractmethod
    def get_content_location(self, item: models.Item) -> str | None:
        """Return location of the content."""

    @abc.abstractmethod
    def get_preview_location(self, item: models.Item) -> str | None:
        """Return location of the preview."""

    @abc.abstractmethod
    def get_thumbnail_location(self, item: models.Item) -> str | None:
        """Return location of the thumbnail."""
