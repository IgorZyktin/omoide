# -*- coding: utf-8 -*-
"""Use cases for search.
"""
from typing import Optional

import omoide.domain.models
from omoide import domain
from omoide.application import app_models
from omoide.domain import dtos
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.domain import models
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_browse
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_search
from omoide.domain.special_types import Result
from omoide.domain.special_types import Success

__all__ = [
    'ApiSearchUseCase',
    'ApiSuggestTagUseCase',
]


class ApiSearchUseCase:
    """Use case for search (API)."""

    def __init__(
            self,
            search_repo: in_rp_search.AbsSearchRepository,
            browse_repo: in_rp_browse.AbsBrowseRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo
        self.browse_repo = browse_repo

    async def execute(
            self,
            user: omoide.domain.models.User,
            aim: app_models.Aim,
    ) -> Result[errors.Error, tuple[list[models.Item], list[Optional[str]]]]:
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


class ApiSuggestTagUseCase:
    """Help user by suggesting possible tags."""

    def __init__(
            self,
            search_repo: in_rp_search.AbsSearchRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo

    async def execute(
            self,
            user: omoide.domain.models.User,
            guess: dtos.GuessTag,
    ) -> Result[errors.Error, list[dtos.GuessResult]]:
        """Return possible tags."""
        obligation = dtos.Obligation(max_results=10)

        async with self.search_repo.transaction():
            if user.is_registered:
                variants = await self.search_repo \
                    .guess_tag_known(user, guess, obligation)
            else:
                variants = await self.search_repo \
                    .guess_tag_anon(user, guess, obligation)

        return Success(variants)
