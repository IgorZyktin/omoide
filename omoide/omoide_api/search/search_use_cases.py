"""Use cases that process commands from users."""
from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase


class AutocompleteUseCase(BaseAPIUseCase):
    """Use case for suggesting tag autocomplete."""

    async def execute(
        self,
        user: models.User,
        tag: str,
        minimal_length: int,
        limit: int,
    ) -> list[str]:
        """Execute."""
        if len(tag) < minimal_length:
            return []

        repo = self.mediator.search_repo
        async with self.mediator.storage.transaction():
            if user.is_anon:
                variants = await repo.autocomplete_tag_anon(tag=tag,
                                                            limit=limit)
            else:
                variants = await repo.autocomplete_tag_known(user=user,
                                                             tag=tag,
                                                             limit=limit)
        return variants


class RecentUpdatesUseCase(BaseAPIUseCase):
    """Use case for getting recently updated items."""

    async def execute(
        self,
        user: models.User,
        last_seen: int,
        limit: int,
    ) -> tuple[list[models.Item], list[str | None]]:
        """Execute."""
        self.ensure_not_anon(user, operation='read recently updated items')

        async with self.mediator.storage.transaction():
            items = await self.mediator.browse_repo.get_recently_updated_items(
                user=user,
                last_seen=last_seen,
                limit=limit,
            )
            names = await self.mediator.browse_repo.get_parent_names(items)

        return items, names
