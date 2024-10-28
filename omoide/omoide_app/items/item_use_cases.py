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


class AppUpdateItemUseCase(BaseAPPUseCase):
    """Use case for item modification page."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> tuple[models.Item, int, list[models.User], list[str], models.Metainfo | None]:
        """Execute."""
        if user.is_anon:
            msg = 'You are not allowed to update items'
            raise exceptions.AccessDeniedError(msg)

        async with self.mediator.database.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)

            total = await self.mediator.items_repo.count_all_children_of(item)
            can_see = await self.mediator.users_repo.get_users(
                uuids=item.permissions,
            )
            computed_tags = await self.mediator.items_repo.read_computed_tags(item_uuid)
            metainfo = await self.mediator.meta_repo.read_metainfo(item)

        return item, total, can_see, computed_tags, metainfo


class AppDeleteItemUseCase(BaseAPPUseCase):
    """Use case for item deletion page."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> tuple[models.Item, int]:
        """Execute."""
        if user.is_anon:
            msg = 'You are not allowed to delete items'
            raise exceptions.AccessDeniedError(msg)

        async with self.mediator.database.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)

            if item.owner_uuid != user.uuid and user.is_not_admin:
                msg = 'You must own item {item_uuid} to delete it'
                raise exceptions.AccessDeniedError(msg, item_uuid=item_uuid)

            total = await self.mediator.items_repo.count_all_children_of(item)

        return item, total
