"""Use cases for search."""
from omoide import domain
from omoide import models
from omoide.omoide_api.common.use_cases import BaseAPIUseCase


class ApiSearchUseCase(BaseAPIUseCase):
    """Use case for search (API)."""

    async def execute(
        self,
        user: models.User,
        aim: domain.Aim,
    ) -> tuple[list[domain.Item], list[[str | None]]]:
        """Perform search request."""
        if not aim.query:
            return [], []

        async with self.mediator.storage.transaction():
            items = await self.mediator.search_repo \
                .get_matching_items(user, aim, limit=1000)
            names = await self.mediator.browse_repo.get_parents_names(items)
        return items, names


class AppDynamicSearchUseCase(BaseAPIUseCase):
    """Use case for dynamic search."""

    async def execute(
        self,
        user: models.User,
        aim: domain.Aim,
    ) -> int:
        """Return amount of items that correspond to query (not items)."""
        total = 0
        async with self.mediator.storage.transaction():
            if aim.query:
                total = await self.mediator.search_repo.count_matching_items(
                    user=user,
                    aim=aim,
                )

        return total


class AppPagedSearchUseCase(BaseAPIUseCase):
    """Use case for paged search."""

    async def execute(
        self,
        user: models.User,
        aim: domain.Aim,
    ) -> tuple[list[domain.Item], list[str | None]]:
        """Return items that correspond to query."""
        items = []
        names = []
        async with self.mediator.storage.transaction():
            if aim.query:
                items = await self.mediator.search_repo \
                    .get_matching_items(user, aim, limit=1000)
                names = await self.mediator.browse_repo.get_parents_names(
                    items)

        return items, names
