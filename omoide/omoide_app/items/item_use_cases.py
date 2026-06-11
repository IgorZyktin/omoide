"""Use case for item operations."""

from uuid import UUID

from omoide import const
from omoide import exceptions
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase


class AppCreateItemUseCase:
    """Use case for item creation page."""

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
    ) -> tuple[models.Item, list[models.User]]:
        """Execute."""
        async with self.database.transaction() as conn:
            if parent_uuid == const.DUMMY_UUID:
                parent = await self.users.get_root_item(conn, user)
            else:
                parent = await self.items.get_by_uuid(conn, parent_uuid)

                if parent.owner_uuid != user.uuid:
                    msg = 'You are not allowed to create items for other users'
                    raise exceptions.AccessDeniedError(msg)

            users_with_permission = await self.users.select(
                conn=conn,
                ids=parent.permissions,
            )

        return parent, users_with_permission


class AppUpdateItemUseCase:
    """Use case for item modification page."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.items = items
        self.users = users
        self.meta = meta

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> tuple[
        models.Item, int, list[models.User], list[str], models.Metainfo | None, dict[str, str]
    ]:
        """Execute."""
        if user.is_anon:
            msg = 'You are not allowed to update items'
            raise exceptions.AccessDeniedError(msg)

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            total = await self.items.count_family(conn, item)
            can_see = await self.users.select(conn, ids=item.permissions)
            computed_tags = await self.items.get_computed_tags(conn, item)
            metainfo = await self.meta.get_by_item(conn, item)
            notes = await self.meta.get_item_notes(conn, item)

        return item, total, can_see, computed_tags, metainfo, notes


class AppDeleteItemUseCase:
    """Use case for item deletion page."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.items = items

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> tuple[models.Item, int]:
        """Execute."""
        if user.is_anon:
            msg = 'You are not allowed to delete items'
            raise exceptions.AccessDeniedError(msg)

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)

            if item.owner_uuid != user.uuid and user.is_not_admin:
                msg = 'You must own item {item_uuid} to delete it'
                raise exceptions.AccessDeniedError(msg, item_uuid=item_uuid)

            total = await self.items.count_family(conn, item)

        return item, total
