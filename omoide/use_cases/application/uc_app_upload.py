"""Use case for upload."""
from uuid import UUID

from omoide import domain
from omoide import models
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.storage.interfaces.repositories.abs_users_repo import AbsUsersRepo


__all__ = [
    'AppUploadUseCase',
]


class AppUploadUseCase:
    """Use case for upload."""

    def __init__(
            self,
            users_repo: AbsUsersRepo,
            items_repo: interfaces.AbsItemsRepo,
    ) -> None:
        """Initialize instance."""
        self.users_repo = users_repo
        self.items_repo = items_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: models.User,
            uuid: UUID,
    ) -> Result[errors.Error, tuple[domain.Item, list[models.User]]]:
        """Return preview model suitable for rendering."""
        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid,
                                               actions.Item.UPDATE)
            if error:
                return Failure(error)

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            can_see = await self.users_repo.read_filtered_users(
                *item.permissions
            )

        return Success((item, can_see))
