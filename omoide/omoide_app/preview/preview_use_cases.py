"""Use cases for preview."""

from typing import NamedTuple
from uuid import UUID

from omoide import exceptions
from omoide import models
from omoide.omoide_app.common.common_use_cases import BaseAPPUseCase


class PreviewResult(NamedTuple):
    """Result of a request for a single item."""

    item: models.Item
    parents: list[models.Item]
    metainfo: models.Metainfo
    siblings: list[models.Item]
    all_tags: set[str]


class AppPreviewUseCase(BaseAPPUseCase):
    """Use case for item preview."""

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> PreviewResult:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            public_users = await self.mediator.users.get_public_user_ids(conn)

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

            metainfo = await self.mediator.meta.get_by_item(conn, item)
            parents = await self.mediator.items.get_parents(conn, item)
            siblings = await self.mediator.items.get_siblings(conn, item)

            all_tags: set[str] = set()
            all_tags.update(item.tags)
            for parent in parents:
                all_tags.update(parent.tags)

        result = PreviewResult(
            item=item,
            parents=parents,
            metainfo=metainfo,
            siblings=siblings,
            all_tags=all_tags,
        )

        return result
