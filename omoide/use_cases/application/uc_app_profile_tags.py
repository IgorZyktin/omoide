"""Use case for user profile tags."""
from omoide import models
from omoide.domain import errors
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.storage import interfaces as storage_interfaces

__all__ = [
    'AppProfileTagsUseCase',
]


class AppProfileTagsUseCase:
    """Use case for user profile tags."""

    def __init__(
            self,
            search_repo: storage_interfaces.AbsSearchRepository,
    ) -> None:
        """Initialize instance."""
        self.search_repo = search_repo

    async def execute(
            self,
            user: models.User,
    ) -> Result[errors.Error, list[tuple[str, int]]]:
        """Return tags with their counters."""
        async with self.search_repo.transaction():
            known_tags = await self.search_repo.count_all_tags(user)
        return Success(known_tags)
