"""Use cases for uploading."""

from typing import NamedTuple
from uuid import UUID

from omoide import exceptions
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase


class UploadPage(NamedTuple):
    """Pre-filled context for the upload page."""

    item: models.Item
    users_with_permission: list[models.User]


class AppUploadUseCase:
    """Use case for uploading."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.items = items
        self.users = users

    async def execute(
        self,
        user: models.User,
        parent_uuid: UUID,
    ) -> UploadPage:
        """Execute."""
        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, parent_uuid)

            if item.owner_uuid != user.uuid and not user.is_admin:
                msg = 'You are not allowed to upload for different user'
                raise exceptions.NotAllowedError(msg)

            users_with_permission = await self.users.select(conn, ids=item.permissions)

        return UploadPage(item=item, users_with_permission=users_with_permission)
