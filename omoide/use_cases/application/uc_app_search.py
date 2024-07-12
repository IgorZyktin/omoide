"""Use cases for search."""
from typing import Optional

from omoide import domain
from omoide import models
from omoide.domain import errors
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.storage import interfaces as storage_interfaces

__all__ = [
    'AppDynamicSearchUseCase',
    'AppPagedSearchUseCase',
]


class BaseSearchUseCase:
    """Base case for all search use cases."""

    def __init__(
            self,
            search_repo: storage_interfaces.AbsSearchRepository,
            browse_repo: storage_interfaces.AbsBrowseRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo
        self.browse_repo = browse_repo


class AppDynamicSearchUseCase(BaseSearchUseCase):
    """Use case for dynamic search."""

    async def execute(
            self,
            user: models.User,
            aim: domain.Aim,
    ) -> Result[errors.Error, int]:
        """Return amount of items that correspond to query (not items)."""
        async with self.search_repo.transaction():
            total = 0
            if aim.query:
                total = await self.search_repo.count_matching_items(user, aim)
        return Success(total)


class AppPagedSearchUseCase(BaseSearchUseCase):
    """Use case for paged search."""

    async def execute(
            self,
            user: models.User,
            aim: domain.Aim,
    ) -> Result[errors.Error, tuple[list[domain.Item], list[Optional[str]]]]:
        """Return items that correspond to query."""
        async with self.search_repo.transaction():
            items = []
            if aim.query:
                obligation = domain.Obligation(max_results=1000)
                items = await self.search_repo \
                    .get_matching_items(user, aim, obligation)
                names = await self.browse_repo.get_parents_names(items)
        return Success((items, names))
