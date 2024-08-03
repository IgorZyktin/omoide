"""Object storage that saves data into files."""
from omoide import const
from omoide import models
from omoide import utils
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

    async def save(
        self,
        item: models.Item,
        media_type: const.MEDIA_TYPE,
        binary_content: bytes,
        ext: str,
    ) -> None:
        """Save object and return operation id."""
        media = models.Media(
            id=-1,
            created_at=utils.now(),
            processed_at=None,
            error=None,
            owner_uuid=item.owner_uuid,
            item_uuid=item.uuid,
            media_type=media_type,
            content=binary_content,
            ext=ext,
        )
        await self.media_repo.create_media(media)

    async def delete(self) -> None:
        """Delete object."""

    async def copy(self) -> None:
        """Copy object."""
