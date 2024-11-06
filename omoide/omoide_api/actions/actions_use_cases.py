"""Use cases for heavy operations."""

from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class RebuildKnownTagsAnonUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for anon."""

    async def execute(self, admin: models.User) -> int:
        """Initiate serial operation execution."""
        self.ensure_admin(admin, subject='known tags for anon')

        async with self.mediator.database.transaction() as conn:
            LOG.info('{} is rebuilding known tags for anon', admin)

            operation_id = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_ANON,
            )

        return operation_id


class RebuildKnownTagsUserUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for known user."""

    async def execute(self, admin: models.User, user_uuid: UUID) -> int:
        """Initiate serial operation execution."""
        self.ensure_admin(admin, subject=f'known tags for user {user_uuid}')

        async with self.mediator.database.transaction() as conn:
            user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            LOG.info('{} is rebuilding known tags for {}', admin, user)

            operation_id = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_USER,
                extras={'user_id': user.id},
            )

        return operation_id


class RebuildKnownTagsAllUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for all registered users."""

    async def execute(self, admin: models.User) -> int:
        """Initiate serial operation execution."""
        self.ensure_admin(admin, subject='known tags for all registered users')

        async with self.mediator.database.transaction() as conn:
            LOG.info('{} is rebuilding known tags for all users', admin)

            operation_id = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name=const.AllSerialOperations.REBUILD_KNOWN_TAGS_ALL,
            )

        return operation_id


class RebuildComputedTagsUseCase(BaseAPIUseCase):
    """Use case for rebuilding computed tags."""

    affected_target = 'computed tags'

    async def execute(
        self,
        admin: models.User,
        user_uuid: UUID,
    ) -> tuple[models.User, models.Item, int]:
        """Prepare for execution."""
        self.ensure_admin(admin, subject=self.affected_target)

        async with self.mediator.database.transaction() as conn:
            owner = await self.mediator.users.get_by_uuid(conn, user_uuid)
            item = await self.mediator.users.get_root_item(conn, owner)

            LOG.info(
                '{} is rebuilding {} for item {} (owner is {})',
                admin,
                self.affected_target,
                item,
                owner,
            )

            operation_id = await self.mediator.misc.create_serial_operation(
                conn=conn,
                name=const.AllSerialOperations.REBUILD_ITEM_TAGS,
                extras={
                    'item_id': item.id,
                    'apply_to_children': True,
                    'apply_to_owner': True,
                    'apply_to_permissions': True,
                    'apply_to_anon': True,
                },
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
        self.ensure_not_anon(user, operation='copy image for item')

        if source_uuid == target_uuid:
            return []

        async with self.mediator.database.transaction() as conn:
            source = await self.mediator.items.get_by_uuid(conn, source_uuid)
            target = await self.mediator.items.get_by_uuid(conn, target_uuid)

            self.ensure_admin_or_owner(user, source, subject='item images')
            self.ensure_admin_or_owner(user, target, subject='item images')

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
