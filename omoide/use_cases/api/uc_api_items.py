"""Use case for items."""

from uuid import UUID

from omoide import custom_logging
from omoide import exceptions
from omoide import interfaces
from omoide import models
from omoide import serial_operations as so
from omoide.domain import actions
from omoide.storage import interfaces as storage_interfaces

__all__ = [
    'ApiItemUpdateParentUseCase',
]

LOG = custom_logging.get_logger(__name__)


class BaseItemMediaUseCase:
    """Base use case."""

    def __init__(
        self,
        policy: interfaces.AbsPolicy,
        items_repo: storage_interfaces.AbsItemsRepo,
        metainfo_repo: storage_interfaces.AbsMetainfoRepo,
        media_repo: storage_interfaces.AbsMediaRepo,
    ) -> None:
        """Initialize instance."""
        self.policy = policy
        self.items_repo = items_repo
        self.metainfo_repo = metainfo_repo
        self.media_repo = media_repo


class ApiItemUpdateParentUseCase(BaseItemMediaUseCase):
    """Use case for changing parent item."""

    def __init__(
        self,
        policy: interfaces.AbsPolicy,
        users_repo: storage_interfaces.AbsUsersRepo,
        items_repo: storage_interfaces.AbsItemsRepo,
        metainfo_repo: storage_interfaces.AbsMetainfoRepo,
        media_repo: storage_interfaces.AbsMediaRepo,
        misc_repo: storage_interfaces.AbsMiscRepo,
    ) -> None:
        """Initialize instance."""
        super().__init__(policy, items_repo, metainfo_repo, media_repo)
        self.users_repo = users_repo
        self.misc_repo = misc_repo

    async def execute(
        self,
        policy: interfaces.AbsPolicy,
        user: models.User,
        uuid: UUID,
        new_parent_uuid: UUID,
    ) -> UUID:
        """Execute."""
        if uuid == new_parent_uuid:
            return new_parent_uuid

        async with self.items_repo.transaction():
            error = await policy.is_restricted(user, uuid, actions.Item.UPDATE)
            if error:
                msg = 'You cannot do it'
                raise exceptions.NotAllowedError(msg)

            error = await policy.is_restricted(
                user, new_parent_uuid, actions.Item.UPDATE
            )
            if error:
                msg = 'You cannot do it'
                raise exceptions.NotAllowedError(msg)

            is_child = await self.items_repo.check_child(uuid, new_parent_uuid)
            if is_child:
                msg = 'You cannot do it'
                raise exceptions.NotAllowedError(msg)

            item = await self.items_repo.get_item(uuid)

            # if item.parent_uuid is not None:
            #     old_parent = await self.items_repo.get_item(item.parent_uuid)

            item.parent_uuid = new_parent_uuid
            await self.items_repo.update_item(item)

            new_parent = await self.items_repo.get_item(new_parent_uuid)

            if not new_parent.thumbnail_ext and item.thumbnail_ext:
                LOG.warning(
                    'Supposed to copy image from {} to {}',
                    item,
                    new_parent,
                )

            operation = so.UpdateTagsSO(
                extras={
                    'item_uuid': str(uuid),
                    'apply_to_children': True,
                },
            )
            operation_id = await self.misc_repo.create_serial_operation(
                operation
            )

        return new_parent_uuid
