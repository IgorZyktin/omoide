"""Use cases for uploading."""

from uuid import UUID

from omoide import exceptions
from omoide import models
from omoide.omoide_app.common.common_use_cases import BaseAPPUseCase


class AppUploadUseCase(BaseAPPUseCase):
    """Use case for uploading."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> tuple[models.Item, list[models.User]]:
        """Execute."""
        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)

            if item.owner_uuid != user.uuid and not user.is_admin:
                msg = 'You are not allowed to upload for different user'
                raise exceptions.NotAllowedError(msg)

            users_with_permission = await self.mediator.users_repo.get_users(
                uuids=item.permissions,
            )

        return item, users_with_permission
