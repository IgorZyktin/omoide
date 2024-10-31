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
        async with self.mediator.database.transaction() as conn:
            if parent_uuid == const.DUMMY_UUID:
                parent = await self.mediator.users.get_root_item(conn, user)
            else:
                parent = await self.mediator.items.get_by_uuid(conn, parent_uuid)

                if parent.owner_uuid != user.uuid:
                    msg = 'You are not allowed to create items for other users'
                    raise exceptions.AccessDeniedError(msg)

            users_with_permission = await self.mediator.users.select(
                conn=conn,
                ids=parent.permissions,
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

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            total = await self.mediator.items.count_family(conn, item)
            can_see = await self.mediator.users.select(conn, ids=item.permissions)
            computed_tags = await self.mediator.items.read_computed_tags(conn, item)
            metainfo = await self.mediator.meta.get_by_item(conn, item)

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

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)

            if item.owner_uuid != user.uuid and user.is_not_admin:
                msg = 'You must own item {item_uuid} to delete it'
                raise exceptions.AccessDeniedError(msg, item_uuid=item_uuid)

            total = await self.mediator.items.count_family(conn, item)

        return item, total
