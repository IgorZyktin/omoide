"""Use case for home page."""
from typing import Optional

from omoide import domain
from omoide import models
from omoide.domain import interfaces
from omoide.infra.special_types import Success

__all__ = [
    'AppHomeUseCase',
]


class AppHomeUseCase:
    """Use case for home page."""

    def __init__(self, browse_repo: interfaces.AbsBrowseRepository) -> None:
        """Initialize instance."""
        self.browse_repo = browse_repo

    async def execute(
            self,
            user: models.User,
            aim: domain.Aim,
    ) -> Success[tuple[list[domain.Item], list[Optional[str]]]]:
        """Perform request for home directory."""
        async with self.browse_repo.transaction():
            items = await self.browse_repo.simple_find_items_to_browse(
                user=user,
                uuid=None,
                aim=aim,
            )
            names = await self.browse_repo.get_parents_names(items)

        return Success((items, names))
