"""Use cases for User-related operations."""
from typing import Any
from uuid import UUID

from omoide import const
from omoide import models
from omoide import utils
from omoide import exceptions
from omoide.omoide_api.common.use_cases import BaseAPIUseCase


class BaseUsersUseCase(BaseAPIUseCase):
    """Base class for user-related use cases."""

    async def _get_target_user(
        self,
        who_asking: models.User,
        uuid: UUID,
    ) -> models.User:
        """Read specified user."""
        if who_asking.is_admin:
            target_user = await self.mediator.users_repo.read_user(uuid)
            # FEATURE - raise right from repository
            if target_user is None:
                msg = 'User with UUID {uuid} does not exist'
                raise exceptions.DoesNotExistError(msg, uuid=uuid)
        else:
            target_user = who_asking

        return target_user


class GetUserStatsUseCase(BaseUsersUseCase):
    """Use case for getting current user stats."""

    async def execute(
        self,
        user: models.User,
        uuid: UUID,
    ) -> dict[str, int | str]:
        """Execute."""
        self.ensure_not_anon(user, target='get user stats')

        empty: dict[str, int | str] = {
            'total_items': 0,
            'total_collections': 0,
            'content_size': 0,
            'content_size_hr': '0 B',
            'preview_size': 0,
            'preview_size_hr': '0 B',
            'thumbnail_size': 0,
            'thumbnail_size_hr': '0 B',
        }

        async with self.mediator.storage.transaction():
            target_user = await self._get_target_user(user, uuid)
            root = await self.mediator.items_repo.read_root_item(target_user)

            if root is None:
                return empty

            size = await (
                self.mediator.users_repo.calc_total_space_used_by(target_user)
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

        return {
            'total_items': total_items,
            'total_collections': total_collections,
            'content_size': size.content_size,
            'content_size_hr': size.content_size_hr,
            'preview_size': size.preview_size,
            'preview_size_hr': size.preview_size_hr,
            'thumbnail_size': size.thumbnail_size,
            'thumbnail_size_hr': size.thumbnail_size_hr,
        }


class GetUserTagsUseCase(BaseUsersUseCase):
    """Use case for getting tags available to the current user."""

    async def execute(
        self,
        user: models.User,
        uuid: str,
    ) -> dict[str, int]:
        """Execute."""
        async with self.mediator.storage.transaction():
            if uuid.lower() == const.ANON:
                tags = await self.mediator.search_repo.count_all_tags_anon()

            elif utils.is_valid_uuid(uuid):
                target_user = await self._get_target_user(user, UUID(uuid))
                tags = await self.mediator.search_repo.count_all_tags_known(
                    user=target_user,
                )

            else:
                msg = 'Given user UUID is not valid'
                raise exceptions.InvalidInputError(msg)

        return tags


class GetAllUsersUseCase(BaseAPIUseCase):
    """Use case for getting all users."""

    async def execute(
        self,
        user: models.User,
        login: str | None,
    ) -> tuple[list[models.User], dict[UUID, UUID | None]]:
        """Execute."""
        self.ensure_not_anon(user, target='get list of users')
        extras: dict[UUID, UUID | None]

        async with self.mediator.storage.transaction():
            if user.is_admin:

                if login:
                    users = await self.mediator.users_repo.read_filtered_users(
                        login=login,
                    )
                else:
                    users = await self.mediator.users_repo.read_all_users()

                roots = await self.mediator.items_repo.read_all_root_items(
                    *users,
                )
                extras = {root.owner_uuid: root.uuid for root in roots}

            else:
                root = await self.mediator.items_repo.read_root_item(user)
                users = [user]
                extras = {user.uuid: root.uuid if root else None}

        return users, extras


class GetUserByUUIDUseCase(BaseUsersUseCase):
    """Use case for getting user by UUID."""

    async def execute(
        self,
        user: models.User,
        uuid: UUID,
    ) -> tuple[models.User, dict[str, Any]]:
        """Execute."""
        self.ensure_not_anon(user, target='get user info')

        async with self.mediator.storage.transaction():
            target_user = await self._get_target_user(user, uuid)
            root = await self.mediator.items_repo.read_root_item(target_user)
            extras = {'root_item': root.uuid if root else None}

        return target_user, extras
