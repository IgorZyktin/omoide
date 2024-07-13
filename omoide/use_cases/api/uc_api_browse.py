"""Use case for browse."""
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide import interfaces
from omoide import models
from omoide.domain import actions
from omoide.domain import errors
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.storage import interfaces as storage_interfaces

__all__ = [
    'APIBrowseUseCase',
]


class APIBrowseUseCase:
    """Use case for browse (api)."""

    def __init__(
        self,
        browse_repo: storage_interfaces.AbsBrowseRepository,
    ) -> None:
        """Initialize instance."""
        self.browse_repo = browse_repo

    async def execute(
        self,
        policy: interfaces.AbsPolicy,
        user: models.User,
        uuid: UUID,
        aim: domain.Aim,
    ) -> Result[errors.Error, tuple[list[domain.Item], list[Optional[str]]]]:
        async with self.browse_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.READ)

            if error:
                return Failure(error)

            if aim.nested:
                items = await self.browse_repo.simple_find_items_to_browse(
                    user=user,
                    uuid=uuid,
                    aim=aim,
                )

            else:
                items = await self.browse_repo.complex_find_items_to_browse(
                    user=user,
                    uuid=uuid,
                    aim=aim,
                )

            names = await self.browse_repo.get_parents_names(items)

        return Success((items, names))
