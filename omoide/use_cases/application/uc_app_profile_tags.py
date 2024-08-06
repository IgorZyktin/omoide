"""Use case for user profile tags."""
from omoide import models
from omoide.infra.mediator import Mediator

__all__ = [
    'AppProfileTagsUseCase',
]


class AppProfileTagsUseCase:
    """Use case for user profile tags."""

    def __init__(self, mediator: Mediator) -> None:
        """Initialize instance."""
        self.mediator = mediator

    async def execute(self, user: models.User) -> dict[str, int]:
        """Return tags with their counters."""
        async with self.mediator.storage.transaction():
            known_tags = await self.mediator.search_repo.count_all_tags_known(
                user=user,
            )
        return known_tags
