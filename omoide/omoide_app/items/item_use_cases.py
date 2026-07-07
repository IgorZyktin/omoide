"""Use case for item operations."""

from typing import NamedTuple
from uuid import UUID

from omoide import const
from omoide import exceptions
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase


class CreateItemPage(NamedTuple):
    """Pre-filled parent context for the create-item page."""

    parent: models.Item
    users_with_permission: list[models.User]


class UpdateItemPage(NamedTuple):
    """Pre-filled context for the edit-item page."""

    item: models.Item
    total: int
    can_see: list[models.User]
    computed_tags: list[str]
    metainfo: models.Metainfo | None
    notes: dict[str, str]


class DeleteItemPage(NamedTuple):
    """Pre-filled context for the delete-item confirmation page."""

    item: models.Item
    total: int


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
    ) -> CreateItemPage:
        """Execute."""
        async with self.database.transaction() as conn:
            if parent_uuid == const.DUMMY_UUID:
                parent = await self.users.get_root_item(conn, user)
            else:
                parent = await self.items.get_by_uuid(conn, parent_uuid)

                if parent.owner_id != user.id:
                    msg = 'You are not allowed to create items for other users'
                    raise exceptions.AccessDeniedError(msg)

            users_with_permission = await self.users.select(
                conn=conn,
                ids=parent.permissions,
            )

        return CreateItemPage(parent=parent, users_with_permission=users_with_permission)


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
    ) -> UpdateItemPage:
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

        return UpdateItemPage(
            item=item,
            total=total,
            can_see=can_see,
            computed_tags=computed_tags,
            metainfo=metainfo,
            notes=notes,
        )


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
    ) -> DeleteItemPage:
        """Execute."""
        if user.is_anon:
            msg = 'You are not allowed to delete items'
            raise exceptions.AccessDeniedError(msg)

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)

            if item.owner_id != user.id and not user.is_admin:
                msg = 'You must own item {item_uuid} to delete it'
                raise exceptions.AccessDeniedError(msg, item_uuid=item_uuid)

            total = await self.items.count_family(conn, item)

        return DeleteItemPage(item=item, total=total)
