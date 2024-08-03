"""Object storage that saves data into files."""
from omoide.storage.interfaces.repositories.abs_media_repo import AbsMediaRepo
from omoide.storage.object_storage.interfaces.abs_object_storage import (
    AbsObjectStorage
)


class FileObjectStorageServer(AbsObjectStorage):
    """Object storage that saves data into files.

    This implementation is server-side. It does not
    actually have access to the filesystem. It can
    only operate with media records on the database.
    """

    def __init__(
        self,
        media_repo: AbsMediaRepo,
        prefix_size: int,
    ) -> None:
        """Initialize instance."""
        self.media_repo = media_repo
        self.prefix_size = prefix_size

    def save(self) -> int:
        """Save object and return operation id."""

    def delete(self) -> int:
        """Delete object and return operation id."""

    def copy(self) -> int:
        """Copy object and return operation id."""
