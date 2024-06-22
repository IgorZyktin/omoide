"""Use cases for current User.
"""
from omoide.domain.core import core_models
from omoide.omoide_api.use_cases.base import BaseAPIUseCase


class GetCurrentUserStatsUseCase(BaseAPIUseCase):
    """Use case for getting current user stats."""

    async def execute(
        self,
        user: core_models.User,
    ) -> dict[str, int]:
        """Execute."""
        empty = {
            'total_items': 0,
            'total_collections': 0,
            'content_bytes': 0,
            'preview_bytes': 0,
            'thumbnail_bytes': 0,
        }

        if user.is_anon() or user.root_item is None:
            return empty

        async with self.mediator.users_repo.transaction():
            root = await self.mediator.items_repo.read_item(user.root_item)

            if root is None:
                return empty

            size = await (
                self.mediator.users_repo.calc_total_space_used_by(user)
            )

            total_items = await (
                self.mediator.items_repo.count_items_by_owner(user)
            )

            total_collections = await (
                self.mediator.items_repo.count_items_by_owner(
                    user,
                    only_collections=True,
                )
            )

        return {
            'total_items': total_items,
            'total_collections': total_collections,
            'content_bytes': size.content_size,
            'preview_bytes': size.preview_size,
            'thumbnail_bytes': size.thumbnail_size,
        }


class GetCurrentUserTagsUseCase(BaseAPIUseCase):
    """Use case for getting tags available to the current user."""

    async def execute(
        self,
        user: core_models.User,
    ) -> dict[str, int]:
        """Execute."""
        async with self.mediator.search_repo.transaction():
            known_tags = await self.mediator.search_repo.count_all_tags(user)
        return dict(known_tags)
