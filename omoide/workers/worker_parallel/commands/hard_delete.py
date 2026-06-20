"""Actually delete all files and the item itself."""

from aiofiles import os
from omoide import custom_logging

from omoide.database.implementations import impl_sqlalchemy
from omoide.infra.locators import FilesystemLocator
from omoide.workers.worker_parallel.commands.base_command import Command
from omoide.workers.worker_parallel.database import ParallelPostgreSQLDatabase
from omoide.workers.worker_parallel.models import ParallelCommand

LOG = custom_logging.get_logger(__name__)


class HardDeleteCommand(Command):
    """Actually delete all files and the item itself."""

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
        warnings: list[str] = []
        item_id = self.dto.extras['item_id']

        async with self.database.transaction() as conn:
            item = await self.items.get_by_id(conn, item_id)
            owner = await self.users.get_by_id(conn, item.owner_id)

        if video_path := self.locator.get_video_location(owner, item):
            try:
                await os.unlink(video_path)
            except FileNotFoundError:
                warnings.append(f'File does not exist: {video_path}')

        if content_path := self.locator.get_content_location(owner, item):
            try:
                await os.unlink(content_path)
            except FileNotFoundError:
                warnings.append(f'File does not exist: {content_path}')

        if preview_path := self.locator.get_preview_location(owner, item):
            try:
                await os.unlink(preview_path)
            except FileNotFoundError:
                warnings.append(f'File does not exist: {preview_path}')

        if thumbnail_path := self.locator.get_thumbnail_location(owner, item):
            try:
                await os.unlink(thumbnail_path)
            except FileNotFoundError:
                warnings.append(f'File does not exist: {thumbnail_path}')

        async with self.database.transaction() as conn:
            await self.items.hard_delete(conn, item)

        return warnings, 0
