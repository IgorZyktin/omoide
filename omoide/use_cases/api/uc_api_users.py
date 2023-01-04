# -*- coding: utf-8 -*-
"""Use cases for users.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.presentation import api_models

__all__ = [
    'CreateUserUseCase',
]


class CreateUserUseCase:
    """Use case for creating a user."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsWriteRepository,
            users_repo: interfaces.AbsUsersWriteRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.users_repo = users_repo

    async def execute(
            self,
            authenticator: interfaces.AbsAuthenticator,
            raw_user: api_models.CreateUserIn,
    ) -> Result[errors.Error, UUID]:
        """Business logic."""
        raw_user.name = raw_user.name or raw_user.login
        password = authenticator.encode_password(raw_user.password)

        async with self.users_repo.transaction():
            raw_user.uuid = await self.users_repo.generate_user_uuid()
            uuid = await self.users_repo.create_user(raw_user, password)

        async with self.users_repo.transaction():
            user = await self.users_repo.read_user(uuid)

            if user is None:
                return Failure(errors.UserDoesNotExist(uuid=uuid))

            item_uuid = await self.items_repo.generate_item_uuid()

            root_item = domain.Item(
                uuid=item_uuid,
                parent_uuid=None,
                owner_uuid=user.uuid,
                name=user.name or user.login,
                is_collection=True,
                number=-1,
                content_ext=None,
                preview_ext=None,
                thumbnail_ext=None,
                tags=[],
                permissions=[],
            )

            await self.items_repo.create_item(user, root_item)
            user.root_item = item_uuid
            await self.users_repo.update_user(user)

        return Success(uuid)
