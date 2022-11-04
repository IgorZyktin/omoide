# -*- coding: utf-8 -*-
"""Use case for search.
"""
from omoide import domain
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success


class AppSearchUseCase:
    """Use case for search."""

    def __init__(
            self,
            search_repo: interfaces.AbsSearchRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo

    async def execute(
            self,
            user: domain.User,
            query: domain.Query,
            details: domain.Details,
    ) -> Result[errors.Error, tuple[domain.Results, bool]]:
        """Perform search request."""
        async with self.search_repo.transaction():
            if user.is_anon():
                result = await self._search_for_anon(query, details)
            else:
                result = await self._search_for_known(user, query, details)

        return Success(result)

    async def _search_for_anon(
            self,
            query: domain.Query,
            details: domain.Details,
    ) -> tuple[domain.Results, bool]:
        """Perform search request for anon user."""
        if query:
            is_random = False
            total_items = await self.search_repo.total_specific_anon(query)
            items = await self.search_repo.search_specific_anon(query, details)

        else:
            is_random = True
            total_items = await self.search_repo.total_random_anon()
            items = await self.search_repo.search_random_anon(query, details)

        result = domain.Results(
            total_items=total_items,
            total_pages=details.calc_total_pages(total_items),
            items=items,
            details=details,
        )

        return result, is_random

    async def _search_for_known(
            self,
            user: domain.User,
            query: domain.Query,
            details: domain.Details,
    ) -> tuple[domain.Results, bool]:
        """Perform search request for known user."""
        total_items = await self.search_repo.total_specific_known(
            user=user,
            query=query,
        )

        if query:
            is_random = False
            items = await self.search_repo.search_specific_known(
                user=user,
                query=query,
                details=details,
            )

        else:
            is_random = True
            items = await self.search_repo.search_random_known(
                user=user,
                query=query,
                details=details,
            )

        result = domain.Results(
            item=None,
            total_items=total_items,
            total_pages=details.calc_total_pages(total_items),
            items=items,
            details=details,
            location=None,
        )

        return result, is_random
