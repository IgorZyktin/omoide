"""Actually delete all files and the item itself."""

from aiofiles import os

from omoide import const
from omoide import custom_logging
from omoide import models

from omoide.infra.locators import FilesystemLocator
from omoide.workers.parallel.commands.base_command import Command
from omoide.workers.parallel.database import ParallelPostgreSQLDatabase
from omoide.models import ParallelCommand
from omoide.database import interfaces as db_interfaces

LOG = custom_logging.get_logger(__name__)


class HardDeleteCommand(Command):
    """Actually delete all files and the item itself."""

    def __init__(
        self,
        dto: ParallelCommand,
        database: ParallelPostgreSQLDatabase,
        users: db_interfaces.AbsUsersRepo,
        items: db_interfaces.AbsItemsRepo,
        locator: FilesystemLocator,
    ) -> None:
        """Initialize instance."""
        super().__init__(dto)
        self.database = database
        self.users = users
        self.items = items
        self.locator = locator

    def get_required_resources(self) -> list[const.LockableResource]:
        """Return resources to lock before execution."""
        return [
            const.LockableResource(const.LockNamespace.ITEMS, self.dto.item_id)
        ]

    async def execute(self) -> int:
        """Start execution of the command."""
        async with self.database.transaction() as conn:
            item = await self.items.get_by_id(
                conn, self.dto.item_id, read_deleted=True
            )
            owner = await self.users.get_by_id(conn, item.owner_id)

        deleted = item.status == models.Status.DELETED

        async with self.database.transaction() as conn:
            await self.items.hard_delete(conn, item)

        paths = [
            path
            for path in (
                self.locator.get_path(
                    owner, item, const.MediaType.VIDEO, deleted=deleted
                ),
                self.locator.get_path(
                    owner, item, const.MediaType.CONTENT, deleted=deleted
                ),
                self.locator.get_path(
                    owner, item, const.MediaType.PREVIEW, deleted=deleted
                ),
                self.locator.get_path(
                    owner, item, const.MediaType.THUMBNAIL, deleted=deleted
                ),
            )
            if path is not None
        ]

        if not paths:
            return 0

        # NOTE: Any general OSError shows critical misconfiguration
        # of the host, so it is not added into exception clause
        for path in paths:
            try:
                await os.unlink(path)
            except FileNotFoundError:
                LOG.warning(
                    'File did not exist, skipping hard-delete: {}', path
                )
            else:
                LOG.debug('Deleted file: {}', path)

        return 0
