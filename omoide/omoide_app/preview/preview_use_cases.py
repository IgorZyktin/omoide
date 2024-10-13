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
        async with self.mediator.storage.transaction():
            item = await self.mediator.items_repo.get_item(item_uuid)
            public_users = (
                await self.mediator.users_repo.get_public_user_uuids()
            )

            allowed_to = any(
                (
                    user.is_admin,
                    item.owner_uuid in public_users,
                    item.owner_uuid == user.uuid,
                    str(user.uuid) in item.permissions,
                )
            )

            if not allowed_to:
                msg = 'You are not allowed to preview this'
                raise exceptions.AccessDeniedError(msg)

            metainfo = await self.mediator.meta_repo.read_metainfo(item)
            parents = await self.mediator.items_repo.get_parents(item)
            siblings = await self.mediator.items_repo.get_siblings(item)

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
