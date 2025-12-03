"""Use cases for heavy operations."""

from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.domain import ensure
from omoide.object_storage import interfaces as os_interfaces

LOG = custom_logging.get_logger(__name__)


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
    ) -> tuple[models.User, models.Item, int]:
        """Prepare for execution."""
        ensure.admin(user, 'Only admins can rebuild computed tags for items')

        async with self.database.transaction() as conn:
            item = await self.items_repo.get_by_uuid(conn, item_uuid)
            owner = await self.users_repo.get_by_uuid(conn, item.owner_uuid)

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

        return owner, item, operation_id


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
        object_storage: os_interfaces.AbsObjectStorage,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.misc_repo = misc_repo
        self.users_repo = users_repo
        self.items_repo = items_repo
        self.meta_repo = meta_repo
        self.object_storage = object_storage

    async def execute(
        self,
        user: models.User,
        source_uuid: UUID,
        target_uuid: UUID,
    ) -> list[const.MEDIA_TYPE]:
        """Execute."""
        ensure.registered(user, 'Only registered users can copy images')

        if source_uuid == target_uuid:
            return []

        async with self.database.transaction() as conn:
            source_item = await self.items_repo.get_by_uuid(conn, source_uuid)
            target_item = await self.items_repo.get_by_uuid(conn, target_uuid)

            ensure.owner(user, source_item, 'Only owner can to copy images')
            ensure.owner(user, target_item, 'Only owner can to copy images')

            owner = await self.users_repo.get_by_id(conn, source_item.owner_id)

        media_types = await self.object_storage.copy_all_objects(
            requested_by=user,
            owner=owner,
            source_item=source_item,
            target_item=target_item,
        )

        async with self.database.transaction() as conn:
            if media_types:
                await self.meta_repo.add_item_note(
                    conn=conn,
                    item=target_item,
                    key='copied_image_from',
                    value=str(source_uuid),
                )

        return media_types
