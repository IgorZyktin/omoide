# -*- coding: utf-8 -*-
"""Use cases for users.
"""
from uuid import UUID

from omoide.domain import interfaces, exceptions
from omoide.presentation import api_models

__all__ = [
    'CreateUserUseCase',
]


class CreateUserUseCase:
    """Use case for creating a user."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsRepository,
            users_repo: interfaces.AbsUsersRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.users_repo = users_repo

    async def execute(
            self,
            raw_user: api_models.CreateUserIn,
    ) -> UUID:
        """Business logic."""
        async with self.users_repo.transaction():
            raw_user.uuid = await self.users_repo.generate_uuid()
            uuid = await self.users_repo.create_user(raw_user)
            user = await self.users_repo.read_user(uuid)

            if user is None:
                raise exceptions.NotFound(f'User {uuid} does not exist')

            item_uuid = await self.items_repo.generate_uuid()
            raw_item = api_models.CreateItemIn(
                uuid=item_uuid,
                parent_uuid=None,
                name=user.name,
                is_collection=True,
                tags=[],
                permissions=[],
            )
            await self.items_repo.create_item(user, raw_item)

        return uuid
