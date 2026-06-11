"""Use cases for preview."""

from typing import NamedTuple
from uuid import UUID

import python_utilz as pu

from omoide import exceptions
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase


class PreviewResult(NamedTuple):
    """Result of a request for a single item."""

    item: models.Item
    parents: list[models.Item]
    metainfo: models.Metainfo
    siblings: list[models.Item]
    all_tags: list[str]


class AppPreviewUseCase:
    """Use case for item preview."""

    def __init__(
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
        tags: db_interfaces.AbsTagsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.items = items
        self.users = users
        self.meta = meta
        self.tags = tags

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> PreviewResult:
        """Execute."""
        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            public_users = await self.users.get_public_user_ids(conn)

            allowed_to = any(
                (
                    user.is_admin,
                    item.owner_id in public_users,
                    item.owner_id == user.id,
                    user.id in item.permissions,
                )
            )

            if not allowed_to:
                msg = 'You are not allowed to preview this'
                raise exceptions.AccessDeniedError(msg)

            metainfo = await self.meta.get_by_item(conn, item)
            parents = await self.items.get_parents(conn, item)
            siblings = await self.items.get_siblings(conn, item, collections=False)
            computed_tags = await self.tags.get_computed_tags(conn, item)

        result = PreviewResult(
            item=item,
            parents=parents,
            metainfo=metainfo,
            siblings=siblings,
            all_tags=[tag for tag in sorted(computed_tags) if not pu.is_valid_uuid(tag)],
        )

        return result
