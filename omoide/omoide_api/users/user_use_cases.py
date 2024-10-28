"""Use cases for User-related operations."""

from typing import Any
from uuid import UUID
from uuid import uuid4

from omoide import const
from omoide import custom_logging
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
    ) -> tuple[models.User, dict[str, Any]]:
        """Execute."""
        self.ensure_admin(admin, subject='users')

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
        )

        encoded_password = self.mediator.authenticator.encode_password(
            given_password=password,
            auth_complexity=const.AUTH_COMPLEXITY,
        )

        async with self.mediator.database.transaction():
            await self.mediator.users.create_user(
                user,
                encoded_password=encoded_password,
                auth_complexity=const.AUTH_COMPLEXITY,
            )

        async with self.mediator.database.transaction():
            item = await self.create_one_item(
                user=user,
                uuid=None,
                parent_uuid=None,
                owner_uuid=user.uuid,
                name=user.name,
                is_collection=True,
                number=None,
                tags=[user.name],
                permissions=[],
            )

            extras = {'root_item': item.uuid}

        return admin, extras


class ChangeUserNameUseCase(BaseAPIUseCase):
    """Use case for updating a user's name."""

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
        new_name: str,
    ) -> tuple[models.User, dict[str, Any]]:
        """Execute."""
        self.ensure_not_anon(user, operation='update user name')

        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            LOG.info(
                'User {} is updating user {} name to {}',
                user,
                target_user,
                new_name,
            )

            await self.mediator.users.update_user(conn, user_uuid, name=new_name)

            root = await self.mediator.users.get_root_item(conn, target_user)
            extras = {'root_item': root.uuid}
            # TODO - after renaming root item
            #  we need to recalculate tags in children

        return target_user, extras


class ChangeUserLoginUseCase(BaseAPIUseCase):
    """Use case for updating a user's login."""

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
        new_login: str,
    ) -> tuple[models.User, dict[str, Any]]:
        """Execute."""
        self.ensure_not_anon(user, operation='update user login')

        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            LOG.info(
                'User {} is updating user {} login to {!r}',
                user,
                target_user,
                new_login,
            )

            await self.mediator.users.update_user(user_uuid, login=new_login)

            root = await self.mediator.users.get_root_item(conn, target_user)
            extras = {'root_item': root.uuid}

        return target_user, extras


class ChangeUserPasswordUseCase(BaseAPIUseCase):
    """Use case for updating a user's password."""

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
        new_password: str,
    ) -> tuple[models.User, dict[str, Any]]:
        """Execute."""
        self.ensure_not_anon(user, operation='update user login')

        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            LOG.info('User {} is updating user {} password', user, target_user)

            pack = await self.mediator.users.get_user_by_login(
                login=target_user.login,
            )
            _, password, auth_complexity = pack

            # TODO - what if new password is the same as previous one?

            encoded_password = self.mediator.authenticator.encode_password(
                given_password=new_password, auth_complexity=auth_complexity
            )

            await self.mediator.users.update_user(user_uuid, password=encoded_password)

            root = await self.mediator.users.get_root_item(conn, target_user)
            extras = {'root_item': root.uuid}

        return target_user, extras


class GetAllUsersUseCase(BaseAPIUseCase):
    """Use case for getting all users."""

    async def execute(
        self,
        user: models.User,
    ) -> tuple[list[models.User], dict[UUID, UUID | None]]:
        """Execute."""
        self.ensure_not_anon(user, operation='get list of users')
        extras: dict[UUID, UUID | None]

        async with self.mediator.database.transaction() as conn:
            if user.is_admin:
                users = await self.mediator.users.select(conn)
                roots = await self.mediator.users.get_all_root_items(
                    *users,
                )
                extras = {root.owner_uuid: root.uuid for root in roots}

            else:
                root = await self.mediator.users.get_root_item(conn, user)
                users = [user]
                extras = {user.uuid: root.uuid}

        return users, extras


class GetUserByUUIDUseCase(BaseAPIUseCase):
    """Use case for getting user by UUID."""

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
    ) -> tuple[models.User, dict[str, Any]]:
        """Execute."""
        self.ensure_not_anon(user, operation='get user info')

        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')
            root = await self.mediator.users.get_root_item(conn, target_user)
            extras = {'root_item': root.uuid}

        return target_user, extras


class GetUserResourceUsageUseCase(BaseAPIUseCase):
    """Use case for getting current user stats."""

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
    ) -> models.ResourceUsage:
        """Execute."""
        self.ensure_not_anon(user, operation='get user stats')

        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            disk_usage = await self.mediator.meta.get_total_disk_usage(target_user)

            total_items = await self.mediator.items.count_items_by_owner(target_user)

            total_collections = await self.mediator.items.count_items_by_owner(
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
            tags = await self.mediator.search.count_all_tags_anon(conn)
        return tags


class GetKnownUserTagsUseCase(BaseAPIUseCase):
    """Use case for getting tags available to specific user."""

    async def execute(self, user: models.User, user_uuid: UUID) -> dict[str, int]:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            target_user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'user tags')
            tags = await self.mediator.search.count_all_tags_known(conn, user=target_user)
        return tags
