"""Use case for preview."""
from uuid import UUID

from omoide import domain
from omoide import models
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.storage import interfaces as storage_interfaces

__all__ = [
    'AppPreviewUseCase',
]


class AppPreviewUseCase:
    """Use case for preview."""

    def __init__(
            self,
            preview_repo: storage_interfaces.AbsPreviewRepository,
            users_repo: storage_interfaces.AbsUsersRepo,
            items_repo: storage_interfaces.AbsItemsRepo,
            meta_repo: storage_interfaces.AbsMetainfoRepo,
    ) -> None:
        """Initialize instance."""
        self.preview_repo = preview_repo
        self.users_repo = users_repo
        self.items_repo = items_repo
        self.meta_repo = meta_repo

    async def execute(
            self,
            policy: interfaces.AbsPolicy,
            user: models.User,
            uuid: UUID,
            aim: domain.Aim,
    ) -> Result[errors.Error, domain.SingleResult]:
        """Return preview model suitable for rendering."""
        async with self.preview_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.READ)

            if error:
                return Failure(error)

            location = await self.preview_repo.get_location(
                user=user,
                uuid=uuid,
                aim=aim,
                users_repo=self.users_repo,
            )

            item = await self.items_repo.read_item(uuid)

            if item is None:
                return Failure(errors.ItemDoesNotExist(uuid=uuid))

            metainfo = await self.meta_repo.read_metainfo(uuid)

            neighbours = await self.preview_repo.get_neighbours(
                user=user,
                uuid=uuid,
            )

            result = domain.SingleResult(
                item=item,
                metainfo=metainfo,
                aim=aim,
                location=location,
                neighbours=neighbours,
            )

        return Success(result)
