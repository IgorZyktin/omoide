"""Only mark files as deleted."""

from aiofiles import os

from omoide import const, models
from omoide import custom_logging

from omoide.database import interfaces as db_interfaces
from omoide.infra.locators import FilesystemLocator
from omoide.workers.parallel.commands.base_command import Command
from omoide.workers.parallel.database import ParallelPostgreSQLDatabase
from omoide.models import ParallelCommand

LOG = custom_logging.get_logger(__name__)


class SoftDeleteCommand(Command):
    """Only mark files as deleted."""

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
            item.status = models.Status.DELETED
            await self.items.save(conn, item)

        all_segments = [
            segments
            for segments in (
                self.locator.get_path_segments(
                    owner,
                    item,
                    const.MediaType.VIDEO,
                ),
                self.locator.get_path_segments(
                    owner,
                    item,
                    const.MediaType.CONTENT,
                ),
                self.locator.get_path_segments(
                    owner,
                    item,
                    const.MediaType.PREVIEW,
                ),
                self.locator.get_path_segments(
                    owner,
                    item,
                    const.MediaType.THUMBNAIL,
                ),
            )
            if segments is not None
        ]

        if not all_segments:
            return 0

        # NOTE: Any general OSError shows critical misconfiguration
        # of the host, so it is not added into exception clause
        for segments in all_segments:
            _root, _media, _uuid, _prefix, _filename = segments
            old_path = _root / _media / _uuid / _prefix / _filename
            new_path = self.locator.get_path(owner, item, _media, deleted=True)

            if new_path is None:
                LOG.warning(
                    'Item has no {}, skipping soft-delete: {}',
                    _media,
                    old_path,
                )
                continue

            try:
                await os.rename(
                    src=old_path,
                    dst=new_path,
                )
            except FileNotFoundError:
                LOG.warning(
                    'File did not exist, skipping soft-delete: {}', old_path
                )
            else:
                LOG.debug('Renamed file to deleted: {}', old_path)

        return 0
