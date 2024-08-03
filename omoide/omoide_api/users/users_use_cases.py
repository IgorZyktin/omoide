"""Use cases for User-related operations."""
from typing import Any
from uuid import UUID

from omoide import const
from omoide import domain
from omoide import models
from omoide import custom_logging
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class CreateUserUseCase(BaseAPIUseCase):
    """Use case for creating a new user."""

    async def execute(
        self,
        user: models.User,
        user_in: dict[str, Any],
    ) -> tuple[models.User, dict[str, Any]]:
        """Execute."""
        self.ensure_admin(user, subject='users')

        LOG.info('Admin {} is creating new user {}', user, user_in.get('name'))

        # TODO - make user and items tables less tied
        async with self.mediator.storage.transaction():
            user_uuid = await self.mediator.users_repo.get_free_uuid()
            new_user = models.User(
                uuid=user_uuid,
                name=user_in['name'],
                login=user_in['login'],
                password=self.mediator.authenticator.encode_password(
                    given_password=user_in['password'],
                ),
                role=models.Role.user,
                root_item=None,  # TODO - remove this field
            )

            item_uuid = await self.mediator.items_repo.get_free_uuid()
            new_item = domain.Item(
                uuid=const.DUMMY_UUID,
                parent_uuid=None,
                owner_uuid=user_uuid,
                name=new_user.name,
                is_collection=True,
                number=-1,
            )
            user.root_item = new_item.uuid

            await self.mediator.users_repo.create_user(
                user,
                auth_complexity=const.AUTH_COMPLEXITY,
            )

            item2 = await self.mediator.items_repo.create_item(new_user,
                                                               new_item)
            # TODO - make normal CRUD for metainfo
            await self.mediator.meta_repo.create_empty_metainfo(
                user=new_user,
                item_uuid=item2.uuid,
            )

            extras = {'root_item': item_uuid}

        return user, extras


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

        async with self.mediator.storage.transaction():
            target_user = await self.mediator.users_repo.get_user(user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            LOG.info('User {} is updating user {} name to {}',
                     user, target_user, new_name)

            await self.mediator.users_repo.update_user(
                user_uuid, name=new_name)

            root = await self.mediator.items_repo.get_root_item(target_user)
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

        async with self.mediator.storage.transaction():
            target_user = await self.mediator.users_repo.get_user(user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            LOG.info('User {} is updating user {} login to {!r}',
                     user, target_user, new_login)

            await self.mediator.users_repo.update_user(
                user_uuid, login=new_login)

            root = await self.mediator.items_repo.get_root_item(target_user)
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

        async with self.mediator.storage.transaction():
            target_user = await self.mediator.users_repo.get_user(user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            LOG.info('User {} is updating user {} password', user, target_user)

            encoded_password = (
                self.mediator.authenticator.encode_password(new_password)
            )

            await self.mediator.users_repo.update_user(
                user_uuid, password=encoded_password)

            root = await self.mediator.items_repo.get_root_item(target_user)
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

        async with self.mediator.storage.transaction():
            if user.is_admin:
                users = await self.mediator.users_repo.read_all_users()
                roots = await self.mediator.items_repo.read_all_root_items(
                    *users,
                )
                extras = {root.owner_uuid: root.uuid for root in roots}

            else:
                root = await self.mediator.items_repo.get_root_item(user)
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

        async with self.mediator.storage.transaction():
            target_user = await self.mediator.users_repo.get_user(user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')
            root = await self.mediator.items_repo.get_root_item(target_user)
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

        async with self.mediator.storage.transaction():
            target_user = await self.mediator.users_repo.get_user(user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'users')

            disk_usage = await (
                self.mediator.meta_repo.get_total_disk_usage(target_user)
            )

            total_items = await (
                self.mediator.items_repo.count_items_by_owner(target_user)
            )

            total_collections = await (
                self.mediator.items_repo.count_items_by_owner(
                    target_user,
                    only_collections=True,
                )
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
        async with self.mediator.storage.transaction():
            tags = await self.mediator.search_repo.count_all_tags_anon()
        return tags


class GetKnownUserTagsUseCase(BaseAPIUseCase):
    """Use case for getting tags available to specific user."""

    async def execute(
        self,
        user: models.User,
        user_uuid: UUID,
    ) -> dict[str, int]:
        """Execute."""
        async with self.mediator.storage.transaction():
            target_user = await self.mediator.users_repo.get_user(user_uuid)
            self.ensure_admin_or_owner(user, target_user, 'user tags')
            tags = await self.mediator.search_repo.count_all_tags_known(
                user=target_user,
            )
        return tags
