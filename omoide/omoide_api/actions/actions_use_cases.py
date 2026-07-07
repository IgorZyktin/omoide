"""Use cases for heavy operations."""

from typing import NamedTuple
from uuid import UUID

from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.domain import ensure

LOG = custom_logging.get_logger(__name__)


class RebuildComputedTagsResult(NamedTuple):
    """Enqueued rebuild operation context for an item."""

    owner: models.User
    item: models.Item
    operation_id: int


class BaseActionsUseCase:
    """Base use case class."""

    def __init__(
        self,
        database: db_interfaces.AbsDatabase,
        misc_repo: db_interfaces.AbsMiscRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.misc_repo = misc_repo


class RebuildKnownTagsForAnonUseCase(BaseActionsUseCase):
    """Use case for rebuilding known tags for anon."""

    async def execute(self, user: models.User) -> int:
        """Initiate serial operation execution."""
        ensure.admin(user, 'Only admins can rebuild known tags for anon')

        async with self.database.transaction() as conn:
            LOG.info('{} is rebuilding known tags for anon', user)

            operation_id = await self.misc_repo.create_serial_operation(
                conn=conn,
                name='rebuild_known_tags_for_anon',
                extras={'requested_by': str(user.uuid)},
            )

        return operation_id


class RebuildKnownTagsForUserUseCase:
    """Use case for rebuilding known tags for known user."""

    def __init__(
        self,
        database: db_interfaces.AbsDatabase,
        misc_repo: db_interfaces.AbsMiscRepo,
        users_repo: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.misc_repo = misc_repo
        self.users_repo = users_repo

    async def execute(self, user: models.User, user_uuid: UUID) -> int:
        """Initiate serial operation execution."""
        ensure.admin(user, 'Only admins can rebuild known tags for user')

        async with self.database.transaction() as conn:
            target_user = await self.users_repo.get_by_uuid(conn, user_uuid)
            LOG.info('{} is rebuilding known tags for {}', user, target_user)

            operation_id = await self.misc_repo.create_serial_operation(
                conn=conn,
                name='rebuild_known_tags_for_user',
                extras={
                    'requested_by': str(user.uuid),
                    'user_uuid': str(target_user.uuid),
                },
            )

        return operation_id


class RebuildKnownTagsForAllUseCase(BaseActionsUseCase):
    """Use case for rebuilding known tags for all users."""

    async def execute(self, user: models.User) -> int:
        """Initiate serial operation execution."""
        ensure.admin(user, 'Only admins can rebuild known tags for all users')

        async with self.database.transaction() as conn:
            LOG.info('{} is rebuilding known tags for all users', user)

            # TODO - actual action is not yet implemented
            operation_id = await self.misc_repo.create_serial_operation(
                conn=conn,
                name='rebuild_known_tags_for_all',
                extras={'requested_by': str(user.uuid)},
            )

        return operation_id


class RebuildComputedTagsForItemUseCase:
    """Use case for rebuilding computed tags."""

    def __init__(
        self,
        database: db_interfaces.AbsDatabase,
        misc_repo: db_interfaces.AbsMiscRepo,
        users_repo: db_interfaces.AbsUsersRepo,
        items_repo: db_interfaces.AbsItemsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.misc_repo = misc_repo
        self.users_repo = users_repo
        self.items_repo = items_repo

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> RebuildComputedTagsResult:
        """Prepare for execution."""
        ensure.admin(user, 'Only admins can rebuild computed tags for items')

        async with self.database.transaction() as conn:
            item = await self.items_repo.get_by_uuid(conn, item_uuid)
            owner = await self.users_repo.get_by_id(conn, item.owner_id)

            LOG.info(
                '{} is rebuilding computed tags for item {} (owner is {})',
                user,
                item,
                owner,
            )

            operation_id = await self.misc_repo.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(item_uuid),
                },
            )

        return RebuildComputedTagsResult(owner=owner, item=item, operation_id=operation_id)


class RebuildComputedTagsForAllUseCase(BaseActionsUseCase):
    """Use case for rebuilding computed tags for all users."""

    async def execute(self, user: models.User) -> int:
        """Initiate serial operation execution."""
        ensure.admin(user, 'Only admins can rebuild computed tags for all users')

        async with self.database.transaction() as conn:
            LOG.info('{} is rebuilding computed tags for all users', user)

            operation_id = await self.misc_repo.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags_for_all',
                extras={'requested_by': str(user.uuid)},
            )

        return operation_id


class CopyImageUseCase:
    """Copy image from one item to another."""

    def __init__(
        self,
        database: db_interfaces.AbsDatabase,
        misc_repo: db_interfaces.AbsMiscRepo,
        users_repo: db_interfaces.AbsUsersRepo,
        items_repo: db_interfaces.AbsItemsRepo,
        meta_repo: db_interfaces.AbsMetaRepo,
        commands_repo: db_interfaces.AbsCommandsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.misc_repo = misc_repo
        self.users_repo = users_repo
        self.items_repo = items_repo
        self.meta_repo = meta_repo
        self.commands_repo = commands_repo

    async def execute(
        self,
        user: models.User,
        source_uuid: UUID,
        target_uuid: UUID,
    ) -> None:
        """Execute."""
        ensure.registered(user, 'Only registered users can copy images')

        if source_uuid == target_uuid:
            return

        async with self.database.transaction() as conn:
            source_item = await self.items_repo.get_by_uuid(conn, source_uuid)
            if source_item.status == models.Status.DELETED:
                msg = 'You cannot copy from deleted item'
                raise exceptions.NotAllowedError(msg)

            target_item = await self.items_repo.get_by_uuid(conn, target_uuid)
            if target_item.status == models.Status.DELETED:
                msg = 'You cannot copy to deleted item'
                raise exceptions.NotAllowedError(msg)

            ensure.owner(user, source_item, 'You must own item to copy from')
            ensure.owner(user, target_item, 'You must own item to copy to')

            if source_item.thumbnail_ext is None or source_item.preview_ext is None:
                msg = 'Item must have an image to copy'
                raise exceptions.NotAllowedError(msg)

            await self.commands_repo.copy_image(
                conn=conn,
                requested_by=user,
                source_item=source_item,
                target_item=target_item,
            )
