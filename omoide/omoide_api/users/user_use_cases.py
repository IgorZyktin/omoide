"""Use cases for User-related operations."""

from uuid import UUID
from uuid import uuid4

import python_utilz as pu

from omoide import const
from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.domain import ensure
from omoide.infra import interfaces as infra_interfaces
from omoide.omoide_api.items import item_use_cases

LOG = custom_logging.get_logger(__name__)


class CreateUserUseCase:
    """Use case for creating a new user."""

    def __init__(  # noqa: PLR0913
        self,
        authenticator: infra_interfaces.AbsAuthenticator,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
        items: db_interfaces.AbsItemsRepo,
        meta: db_interfaces.AbsMetaRepo,
        tags: db_interfaces.AbsTagsRepo,
    ) -> None:
        """Initialize instance."""
        self.authenticator = authenticator
        self.database = database
        self.users = users
        self.items = items
        self.meta = meta
        self.tags = tags

    async def execute(
        self,
        admin: models.User,
        name: str,
        login: str,
        password: str,
    ) -> models.User:
        """Execute."""
        ensure.admin(admin, 'Only admins can create users')
        LOG.info('Admin {} is creating new user {}', admin, name)

        new_user = models.User(
            id=-1,
            uuid=uuid4(),
            name=name,
            login=login,
            role=models.Role.USER,
            is_public=False,
            registered_at=pu.now(),
            last_login=None,
            timezone=None,
            lang=None,
            extras={},
        )

        encoded_password = self.authenticator.encode_password(
            given_password=password,
            auth_complexity=const.AUTH_COMPLEXITY,
        )

        async with self.database.transaction() as conn:
            await self.users.create(
                conn=conn,
                user=new_user,
                encoded_password=encoded_password,
                auth_complexity=const.AUTH_COMPLEXITY,
            )

            sub_use_case = item_use_cases.CreateOneItemUseCase(
                database=self.database,
                items=self.items,
                users=self.users,
                meta=self.meta,
                tags=self.tags,
            )
            item = await sub_use_case.execute(
                user=admin,
                item_uuid=None,
                parent_uuid=None,
                name=new_user.name,
                is_collection=True,
                number=None,
                tags=[new_user.name],
                permissions=[],
                top_level=True,
            )
            await sub_use_case.update_tags(new_user, item, conn)

        new_user.extras['root_item_uuid'] = item.uuid

        return new_user


class DeleteUserUseCase:
    """Use case for deleting a user."""

    def __init__(
        self,
        database: AbsDatabase,
        users_repo: db_interfaces.AbsUsersRepo,
        items_repo: db_interfaces.AbsItemsRepo,
        meta_repo: db_interfaces.AbsMetaRepo,
        misc_repo: db_interfaces.AbsMiscRepo,
        tags_repo: db_interfaces.AbsTagsRepo,
        commands_repo: db_interfaces.AbsCommandsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users_repo = users_repo
        self.items_repo = items_repo
        self.meta_repo = meta_repo
        self.misc_repo = misc_repo
        self.tags_repo = tags_repo
        self.commands_repo = commands_repo

    async def execute(self, admin: models.User, user_uuid: UUID) -> None:
        """Execute."""
        ensure.admin(admin, 'Only admins can delete users')

        async with self.database.transaction() as conn:
            user = await self.users_repo.get_by_uuid(conn, user_uuid)
            LOG.info('Admin {} is deleting user {}', admin, user)

            # Delete from permissions of all items
            all_visible_items = await self.items_repo.select(
                conn=conn,
                permissions_id=user.id,
            )

            for visible_item in all_visible_items:
                visible_item.permissions.discard(user.id)
                await self.items_repo.save(conn, visible_item)

            # Delete known tags
            await self.tags_repo.drop_known_tags_user(conn, user, only_tags=None)

            # Delete all items
            affected_users: set[int] = set()
            all_items = await self.items_repo.select(conn, owner_id=user.id)
            for item in all_items:
                affected_users.update(item.permissions)
                metainfo = await self.meta_repo.get_by_item(conn, item)
                await self.meta_repo.soft_delete(conn, metainfo)
                await self.items_repo.soft_delete(conn, item)
                await self.commands_repo.hard_delete(
                    conn=conn,
                    requested_by=admin,
                    item=item,
                )

            # Recalculate all affected tags
            for user_id in affected_users:
                affected_user = await self.users_repo.get_by_id(conn, user_id)
                await self.misc_repo.create_serial_operation(
                    conn=conn,
                    name='rebuild_known_tags_for_user',
                    extras={
                        'requested_by': str(admin.uuid),
                        'user_uuid': str(affected_user.uuid),
                    },
                )

            if user.is_public:
                await self.misc_repo.create_serial_operation(
                    conn=conn,
                    name='rebuild_known_tags_for_anon',
                    extras={'requested_by': str(admin.uuid)},
                )


class ChangeUserNameUseCase:
    """Use case for updating a user's name."""

    def __init__(
        self,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
        misc: db_interfaces.AbsMiscRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users = users
        self.misc = misc

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
        new_name: str,
    ) -> models.User:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to change user name')

        async with self.database.transaction() as conn:
            target_user = await self.users.get_by_uuid(conn, user_uuid)
            ensure.represents(
                user,
                target_user,
                "You cannot change someone else's name",
            )

            LOG.info(
                '{} is updating {} name to {}',
                user,
                target_user,
                new_name,
            )

            target_user.name = new_name
            await self.users.save(conn, target_user)

            root = await self.users.get_root_item(conn, target_user)
            target_user.extras['root_item_uuid'] = root.uuid
            await self.misc.create_serial_operation(
                conn=conn,
                name='rebuild_computed_tags',
                extras={
                    'requested_by': str(user.uuid),
                    'item_uuid': str(root.uuid),
                },
            )

        return target_user


class ChangeUserLoginUseCase:
    """Use case for updating a user's login."""

    def __init__(
        self,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users = users

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
        new_login: str,
    ) -> models.User:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to change user login')

        async with self.database.transaction() as conn:
            target_user = await self.users.get_by_uuid(conn, user_uuid)
            ensure.represents(user, target_user, "You cannot change someone else's login")

            LOG.info(
                'User {} is updating user {} login to {!r}',
                user,
                target_user,
                new_login,
            )

            target_user.login = new_login
            await self.users.save(conn, target_user)

            root = await self.users.get_root_item(conn, target_user)
            target_user.extras['root_item_uuid'] = root.uuid

        return target_user


class ChangeUserPasswordUseCase:
    """Use case for updating a user's password."""

    def __init__(
        self,
        authenticator: infra_interfaces.AbsAuthenticator,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.authenticator = authenticator
        self.database = database
        self.users = users

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
        new_password: str,
    ) -> models.User:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to change user password')

        async with self.database.transaction() as conn:
            target_user = await self.users.get_by_uuid(conn, user_uuid)
            ensure.represents(user, target_user, "You cannot change someone else's password")

            LOG.info('User {} is updating user {} password', user, target_user)

            pack = await self.users.get_by_login(conn, target_user.login)

            if not pack:
                msg = 'User with UUID {user_uuid} does not exist'
                raise exceptions.DoesNotExistError(msg, user_uuid=user_uuid)

            _, password, auth_complexity = pack

            encoded_password = self.authenticator.encode_password(
                given_password=new_password, auth_complexity=auth_complexity
            )

            if encoded_password != password:
                await self.users.update_user_password(conn, target_user, encoded_password)

            root = await self.users.get_root_item(conn, target_user)
            target_user.extras['root_item_uuid'] = root.uuid

        return target_user


class GetAllUsersUseCase:
    """Use case for getting all users."""

    def __init__(
        self,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users = users

    async def execute(
        self,
        user: models.User,
    ) -> list[models.User]:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to get list of users')

        async with self.database.transaction() as conn:
            if user.is_admin:
                users = await self.users.select(conn)
                roots = await self.users.get_root_items_map(conn, *users)
                for each_user in users:
                    each_user.extras['root_item_uuid'] = roots.get(each_user.id, const.DUMMY_UUID)
            else:
                root = await self.users.get_root_item(conn, user)
                user.extras['root_item_uuid'] = root.uuid or const.DUMMY_UUID
                users = [user]

        return users


class GetUserByUUIDUseCase:
    """Use case for getting user by UUID."""

    def __init__(
        self,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users = users

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
    ) -> models.User:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to get registered users')

        async with self.database.transaction() as conn:
            target_user = await self.users.get_by_uuid(conn, user_uuid)
            ensure.represents(user, target_user, "You cannot get someone else's info")
            root = await self.users.get_root_item(conn, target_user)
            target_user.extras['root_item_uuid'] = root.uuid

        return target_user


class GetUserResourceUsageUseCase:
    """Use case for getting current user stats."""

    def __init__(
        self,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users = users
        self.meta = meta

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
    ) -> models.ResourceUsage:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to get user stats')

        async with self.database.transaction() as conn:
            target_user = await self.users.get_by_uuid(conn, user_uuid)
            ensure.represents(user, target_user, "You cannot see someone else's resource usage")

            disk_usage = await self.meta.get_total_disk_usage(conn, target_user)
            total_items = await self.users.count_items_by_owner(conn, target_user)
            total_collections = await self.users.count_items_by_owner(
                conn,
                target_user,
                collections=True,
            )

        return models.ResourceUsage(
            user=target_user,
            total_items=total_items,
            total_collections=total_collections,
            disk_usage=disk_usage,
        )


class GetAnonUserTagsUseCase:
    """Use case for getting tags available to anon."""

    def __init__(
        self,
        database: AbsDatabase,
        tags: db_interfaces.AbsTagsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.tags = tags

    async def execute(self) -> dict[str, int]:
        """Execute."""
        async with self.database.transaction() as conn:
            tags = await self.tags.get_known_tags_anon(conn)
        return tags


class GetKnownUserTagsUseCase:
    """Use case for getting tags available to specific user."""

    def __init__(
        self,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
        tags: db_interfaces.AbsTagsRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.users = users
        self.tags = tags

    async def execute(self, user: models.User, user_uuid: UUID) -> dict[str, int]:
        """Execute."""
        ensure.registered(user, 'Anonymous users are not allowed to get known tags for user')

        async with self.database.transaction() as conn:
            target_user = await self.users.get_by_uuid(conn, user_uuid)
            ensure.represents(user, target_user, "You cannot change someone else's known tags")
            tags = await self.tags.get_known_tags_user(conn, user=target_user)
        return tags
