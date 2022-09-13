# -*- coding: utf-8 -*-
"""Use case for items.
"""
from uuid import UUID

from omoide import domain
from omoide import utils
from omoide.domain import errors
from omoide.domain import exceptions
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'AppItemUpdateUseCase',
]


class AppItemUpdateUseCase:
    """Use case for item modification."""

    def __init__(self, repo: interfaces.AbsItemsRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: domain.User,
            uuid: UUID,
    ) -> Result[errors.Error, None]:
        """Business logic."""
        error = None
        if error:
            return Failure(error)
        return Success(None)


class AppItemDeleteUseCase:
    """Use case for deleting an item."""

    def __init__(self, repo: interfaces.AbsItemsRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            raw_uuid: str,
    ) -> tuple[int, domain.Item]:
        """Business logic."""
        if not utils.is_valid_uuid(raw_uuid):
            raise exceptions.IncorrectUUID(f'Bad uuid {raw_uuid!r}')

        uuid = UUID(raw_uuid)
        await self._repo.assert_has_access(user, uuid, only_for_owner=True)
        total = await self._repo.count_all_children(uuid)
        item = await self._repo.read_item(uuid)

        return total, item
