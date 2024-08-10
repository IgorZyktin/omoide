"""Use case for item operations."""

from uuid import UUID

from omoide import const
from omoide import exceptions
from omoide import models
from omoide.omoide_app.common.common_use_cases import BaseAPPUseCase


class AppCreateItemUseCase(BaseAPPUseCase):
    """Use case for item creation page."""

    async def execute(
        self,
        user: models.User,
        parent_uuid: UUID,
    ) -> tuple[models.Item, list[models.User]]:
        """Execute."""
        async with self.mediator.storage.transaction():
            if parent_uuid == const.DUMMY_UUID:
                parent = await self.mediator.items_repo.get_root_item(user)
            else:
                parent = await self.mediator.items_repo.get_item(parent_uuid)

                if parent.owner_uuid != user.uuid:
                    msg = 'You are not allowed to create items for other users'
                    raise exceptions.AccessDeniedError(msg)

            users_with_permission = await self.mediator.users_repo.get_users(
                uuids=parent.permissions,
            )

        return parent, users_with_permission
