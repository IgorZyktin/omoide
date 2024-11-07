"""Use cases for User-related operations."""

from uuid import UUID
from uuid import uuid4

from omoide import const
from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase
from omoide.omoide_api.common.common_use_cases import BaseItemUseCase

LOG = custom_logging.get_logger(__name__)


class CreateUserUseCase(BaseItemUseCase):
    """Use case for creating a new user."""

    async def execute(
        self,
        admin: models.User,
        name: str,
        login: str,
        password: str,
    ) -> models.User:
        """Execute."""
        self.mediator.policy.ensure_admin(admin, to='create users')
        LOG.info('Admin {} is creating new user {}', admin, name)

        user = models.User(
            id=-1,
            uuid=uuid4(),
            name=name,
            login=login,
            role=models.Role.USER,
            is_public=False,
            registered_at=utils.now(),
            last_login=None,
            timezone=None,
            lang=None,
            extras={},
        )

        encoded_password = self.mediator.authenticator.encode_password(
            given_password=password,
            auth_complexity=const.AUTH_COMPLEXITY,
        )

        async with self.mediator.database.transaction() as conn:
            await self.mediator.users.create(
                conn=conn,
                user=user,
                encoded_password=encoded_password,
                auth_complexity=const.AUTH_COMPLEXITY,
            )

        async with self.mediator.database.transaction() as conn:
            item = await self.create_one_item(
                conn=conn,
                user=user,
                uuid=None,
                parent_uuid=None,
                name=user.name,
                is_collection=True,
                number=None,
                tags=[user.name],
                permissions=[],
            )

            user.extras['root_item_uuid'] = item.uuid

        return admin


class ChangeUserNameUseCase(BaseAPIUseCase):
    """Use case for updating a user's name."""

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
        new_name: str,
    ) -> models.User:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to='change user name')

        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            LOG.info(
                '{} is updating {} name to {}',
                user,
                target_user,
                new_name,
            )

            target_user.name = new_name
            await self.mediator.users.save(conn, target_user)

            root = await self.mediator.users.get_root_item(conn, target_user)
            target_user.extras['root_item_uuid'] = root.uuid
            await self.mediator.misc.create_serial_operation(
                conn=conn,
                name=const.AllSerialOperations.REBUILD_ITEM_TAGS,
                extras={
                    'item_id': root.id,
                    'apply_to_children': True,
                    'apply_to_owner': True,
                    'apply_to_permissions': True,
                    'apply_to_anon': True,
                },
            )

        return target_user


class ChangeUserLoginUseCase(BaseAPIUseCase):
    """Use case for updating a user's login."""

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
        new_login: str,
    ) -> models.User:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to='change user login')

        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            LOG.info(
                'User {} is updating user {} login to {!r}',
                user,
                target_user,
                new_login,
            )

            target_user.login = new_login
            await self.mediator.users.save(conn, target_user)

            root = await self.mediator.users.get_root_item(conn, target_user)
            target_user.extras['root_item_uuid'] = root.uuid

        return target_user


class ChangeUserPasswordUseCase(BaseAPIUseCase):
    """Use case for updating a user's password."""

    do_what: str = 'change user password'

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
        new_password: str,
    ) -> models.User:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.mediator.policy.ensure_represents(user, target_user, to=self.do_what)

            LOG.info('User {} is updating user {} password', user, target_user)

            pack = await self.mediator.users.get_by_login(conn, target_user.login)

            if not pack:
                msg = 'User with UUID {user_uuid} does not exist'
                raise exceptions.DoesNotExistError(msg, user_uuid=user_uuid)

            _, password, auth_complexity = pack

            encoded_password = self.mediator.authenticator.encode_password(
                given_password=new_password, auth_complexity=auth_complexity
            )

            if encoded_password != password:
                await self.mediator.users.update_user_password(conn, target_user, encoded_password)

            root = await self.mediator.users.get_root_item(conn, target_user)
            target_user.extras['root_item_uuid'] = root.uuid

        return target_user


class GetAllUsersUseCase(BaseAPIUseCase):
    """Use case for getting all users."""

    do_what: str = 'get list of users'

    async def execute(
        self,
        user: models.User,
    ) -> list[models.User]:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to=self.do_what)

        async with self.mediator.database.transaction() as conn:
            if user.is_admin:
                users = await self.mediator.users.select(conn)
                roots = await self.mediator.users.get_root_items_map(conn, *users)
                for each_user in users:
                    each_user.extras['root_item_uuid'] = roots.get(each_user.id, const.DUMMY_UUID)
            else:
                root = await self.mediator.users.get_root_item(conn, user)
                user.extras['root_item_uuid'] = root.uuid or const.DUMMY_UUID
                users = [user]

        return users


class GetUserByUUIDUseCase(BaseAPIUseCase):
    """Use case for getting user by UUID."""

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
    ) -> models.User:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to='get user info')

        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')
            root = await self.mediator.users.get_root_item(conn, target_user)
            target_user.extras['root_item_uuid'] = root.uuid

        return target_user


class GetUserResourceUsageUseCase(BaseAPIUseCase):
    """Use case for getting current user stats."""

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
    ) -> models.ResourceUsage:
        """Execute."""
        self.mediator.policy.ensure_registered(user, to='get user stats')

        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            disk_usage = await self.mediator.meta.get_total_disk_usage(conn, target_user)

            total_items = await self.mediator.users.count_items_by_owner(conn, target_user)

            total_collections = await self.mediator.users.count_items_by_owner(
                conn,
                target_user,
                collections=True,
            )

        return models.ResourceUsage(
            user_uuid=user_uuid,
            total_items=total_items,
            total_collections=total_collections,
            disk_usage=disk_usage,
        )


class GetAnonUserTagsUseCase(BaseAPIUseCase):
    """Use case for getting tags available to anon."""

    async def execute(self) -> dict[str, int]:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            tags = await self.mediator.tags.count_all_tags_anon(conn)
        return tags


class GetKnownUserTagsUseCase(BaseAPIUseCase):
    """Use case for getting tags available to specific user."""

    async def execute(self, user: models.User, user_uuid: UUID) -> dict[str, int]:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'user tags')
            tags = await self.mediator.tags.count_all_tags_known(conn, user=target_user)
        return tags
