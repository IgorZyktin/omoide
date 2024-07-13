"""Use cases for home page."""
from omoide import domain
from omoide import models
from omoide.omoide_api.common.use_cases import BaseAPIUseCase


class GetHomePageItemsUseCase(BaseAPIUseCase):
    """Use case for filing home page."""

    async def execute(
        self,
        user: models.User,
        aim: domain.Aim,
    ) -> tuple[list[domain.Item], list[str | None]]:
        """Perform request for home directory."""
        async with self.mediator.storage.transaction():
            items = (
                await self.mediator.browse_repo.simple_find_items_to_browse(
                    user=user,
                    uuid=None,
                    aim=aim,
                )
            )
            names = await self.mediator.browse_repo.get_parents_names(items)

        return items, names
