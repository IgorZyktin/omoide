"""Copy image between items."""

import shutil

from omoide import const
from omoide import custom_logging
from aiofiles.os import wrap
from omoide.database.implementations import impl_sqlalchemy
from omoide.infra.locators import FilesystemLocator
from omoide.workers.worker_parallel.commands.base_command import Command
from omoide.workers.worker_parallel.database import ParallelPostgreSQLDatabase
from omoide.models import ParallelCommand

LOG = custom_logging.get_logger(__name__)


class CopyImageCommand(Command):
    """Copy image between items."""

    def __init__(
        self,
        dto: ParallelCommand,
        database: ParallelPostgreSQLDatabase,
        users: impl_sqlalchemy.UsersRepo,
        items: impl_sqlalchemy.ItemsRepo,
        locator: FilesystemLocator,
    ) -> None:
        """Initialize instance."""
        super().__init__(dto)
        self.database = database
        self.users = users
        self.items = items
        self.locator = locator

    async def execute(self) -> tuple[list[str], int]:
        """Start execution of the command."""
        source_item_id = self.dto.extras.get('source_item_id')
        if source_item_id is None:
            msg = 'Missing source item id'
            raise KeyError(msg)
        source_item_id = int(source_item_id)

        target_item_id = self.dto.extras.get('target_item_id')
        if target_item_id is None:
            msg = 'Missing target item id'
            raise KeyError(msg)
        target_item_id = int(target_item_id)

        async with self.database.transaction() as conn:
            source_item = await self.items.get_by_id(conn, source_item_id)
            source_owner = await self.users.get_by_id(
                conn, source_item.owner_id
            )

            target_item = await self.items.get_by_id(conn, target_item_id)
            target_owner = await self.users.get_by_id(
                conn, target_item.owner_id
            )

        async_copyfile = wrap(shutil.copyfile)

        for media in [const.MediaType.PREVIEW, const.MediaType.THUMBNAIL]:
            source_segments = self.locator.get_path_segments(
                owner=source_owner,
                item=source_item,
                media_type=media,
            )

            if source_segments is None:
                msg = f'Item {source_item.uuid} does not have a {media}'
                raise ValueError(msg)

            _root, _media, _uuid, _prefix, _filename = source_segments
            source_path = _root / _media / _uuid / _prefix / _filename

            if media is const.MediaType.PREVIEW:
                ext = source_item.preview_ext
            else:
                ext = source_item.thumbnail_ext

            new_prefix = self.locator.get_prefix(target_item)
            new_filename = self.locator.get_filename(target_item, ext)
            target_path = (
                _root
                / _media
                / str(target_owner.uuid)
                / new_prefix
                / new_filename
            )

            await async_copyfile(
                src=source_path,
                dst=target_path,
            )
            LOG.debug('Copied file: {} to {}', source_path, target_path)

        return [], 0
