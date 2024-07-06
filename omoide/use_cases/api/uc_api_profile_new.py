"""Use case for checking up updates."""
from typing import Optional

from omoide import domain
from omoide import models
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success

__all__ = [
    'APIProfileNewUseCase',
]


class APIProfileNewUseCase:
    """Use case for checking up updates."""

    def __init__(
            self,
            browse_repo: interfaces.AbsBrowseRepository,
    ) -> None:
        """Initialize instance."""
        self.browse_repo = browse_repo

    async def execute(
            self,
            user: models.User,
            aim: domain.Aim,
    ) -> Result[errors.Error, tuple[list[domain.Item], list[Optional[str]]]]:
        async with self.browse_repo.transaction():
            items = await self.browse_repo.get_recent_items(user, aim)
            names = await self.browse_repo.get_parents_names(items)

        return Success((items, names))
