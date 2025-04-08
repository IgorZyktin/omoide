"""Use cases for heavy operations."""

from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class RebuildKnownTagsForAnonUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for anon."""

    async def execute(self, admin: models.User) -> int:
        """Initiate serial operation execution."""
        self.mediator.policy.ensure_admin(admin, to='rebuild known tags for anon')

        async with self.mediator.database.transaction() as conn:
            LOG.info('{} is rebuilding known tags for anon', admin)

            operation_id = await self.mediator.misc.create_serial_operation(
                conn=conn,
                request=models.RebuildKnownTagsForAnonRequest(requested_by_user_id=admin.id),
            )

        return operation_id


class RebuildKnownTagsForUserUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for known user."""

    async def execute(self, admin: models.User, user_uuid: UUID) -> int:
        """Initiate serial operation execution."""
        self.mediator.policy.ensure_admin(admin, to=f'rebuild known tags for user {user_uuid}')

        async with self.mediator.database.transaction() as conn:
            user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            LOG.info('{} is rebuilding known tags for {}', admin, user)

            operation_id = await self.mediator.misc.create_serial_operation(
                conn=conn,
                request=models.RebuildKnownTagsForUserRequest(
                    requested_by_user_id=admin.id,
                    user_id=user.id,
                ),
            )

        return operation_id


class RebuildKnownTagsForAllUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for all users."""

    async def execute(self, admin: models.User) -> int:
        """Initiate serial operation execution."""
        self.mediator.policy.ensure_admin(admin, to='rebuild known tags for all users')

        async with self.mediator.database.transaction() as conn:
            LOG.info('{} is rebuilding known tags for all users', admin)

            operation_id = await self.mediator.misc.create_serial_operation(
                conn=conn,
                request=models.RebuildKnownTagsForAllRequest(requested_by_user_id=admin.id),
            )

        return operation_id


class RebuildComputedTagsForItemUseCase(BaseAPIUseCase):
    """Use case for rebuilding computed tags."""

    async def execute(
        self,
        admin: models.User,
        item_uuid: UUID,
    ) -> tuple[models.User, models.Item, int]:
        """Prepare for execution."""
        self.mediator.policy.ensure_admin(admin, to=f'rebuild computed tags for item {item_uuid}')

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            owner = await self.mediator.users.get_by_uuid(conn, item.owner_uuid)

            LOG.info(
                '{} is rebuilding computed tags for item {} (owner is {})',
                admin,
                item,
                owner,
            )

            operation_id = await self.mediator.misc.create_serial_operation(
                conn=conn,
                request=models.RebuildComputedTagsForItemRequest(
                    requested_by_user_id=admin.id,
                    item_id=item.id,
                ),
            )

        return owner, item, operation_id


class CopyImageUseCase(BaseAPIUseCase):
    """Copy image from one item to another."""

    async def execute(
        self,
        user: models.User,
        source_uuid: UUID,
        target_uuid: UUID,
    ) -> list[const.MEDIA_TYPE]:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to='copy image for item')

        if source_uuid == target_uuid:
            return []

        async with self.mediator.database.transaction() as conn:
            source = await self.mediator.items.get_by_uuid(conn, source_uuid)
            target = await self.mediator.items.get_by_uuid(conn, target_uuid)

            self.mediator.policy.ensure_can_change(user, source, to='copy images')
            self.mediator.policy.ensure_can_change(user, target, to='copy images')

        media_types = await self.mediator.object_storage.copy_all_objects(
            source_item=source,
            target_item=target,
        )

        async with self.mediator.database.transaction() as conn:
            if media_types:
                await self.mediator.meta.add_item_note(
                    conn=conn,
                    item=target,
                    key='copied_image_from',
                    value=str(source_uuid),
                )

        return media_types
