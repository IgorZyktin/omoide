# -*- coding: utf-8 -*-
"""Repository interfaces.
"""
import abc

from omoide.domain import auth
from omoide.domain import search


class AbsSearchRepository(abc.ABC):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def search_random_items_for_anon_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find random items for unauthorised user."""

    @abc.abstractmethod
    async def search_random_items_for_known_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find random items for authorised user."""

    @abc.abstractmethod
    async def search_specific_items_for_anon_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find specific items for unauthorised user."""

    @abc.abstractmethod
    async def search_specific_items_for_known_user(
            self,
            user: auth.User,
            query: search.Query,
    ) -> search.Result:
        """Find specific items for authorised user."""
