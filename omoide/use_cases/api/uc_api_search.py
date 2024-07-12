"""Use cases for search.
"""
from typing import Optional

from omoide import domain
from omoide import models
from omoide.domain import errors
from omoide.storage import interfaces as storage_interfaces
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'ApiSearchUseCase',
]


class ApiSearchUseCase:
    """Use case for search (API)."""

    def __init__(
            self,
            search_repo: storage_interfaces.AbsSearchRepository,
            browse_repo: storage_interfaces.AbsBrowseRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo
        self.browse_repo = browse_repo

    async def execute(
            self,
            user: models.User,
            aim: domain.Aim,
    ) -> Result[errors.Error, tuple[list[domain.Item], list[Optional[str]]]]:
        """Perform search request."""
        if not aim.query:
            return Success(([], []))

        assert not aim.paged

        obligation = domain.Obligation(max_results=1000)
        async with self.search_repo.transaction():
            items = await self.search_repo \
                .get_matching_items(user, aim, obligation)
            names = await self.browse_repo.get_parents_names(items)
        return Success((items, names))
