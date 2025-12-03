"""Repository that performs all search queries."""

import abc
from typing import Generic
from typing import TypeVar

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsSearchRepo(abc.ABC, Generic[ConnectionT]):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def count(self, conn: ConnectionT, user: models.User, plan: models.Plan) -> int:
        """Return total amount of items relevant to this search query."""

    @abc.abstractmethod
    async def search(
        self,
        conn: ConnectionT,
        user: models.User,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return matching items for search query."""

    @abc.abstractmethod
    async def get_home_items_for_anon(
        self,
        conn: ConnectionT,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return home items for anon."""

    @abc.abstractmethod
    async def get_home_items_for_known(
        self,
        conn: ConnectionT,
        user: models.User,
        plan: models.Plan,
    ) -> list[models.Item]:
        """Return home items for known user."""
