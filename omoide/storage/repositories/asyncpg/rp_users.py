# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on users and their data.
"""
from uuid import UUID
from uuid import uuid4

import sqlalchemy as sa

from omoide import domain
from omoide.domain import interfaces
from omoide.presentation import api_models
from omoide.storage.database import models
from omoide.storage.repositories \
    .asyncpg.rp_users_read import UsersReadRepository


class UsersRepository(
    interfaces.AbsUsersRepository,
    UsersReadRepository,
):
    """Repository that perform CRUD operations on users and their data."""

    async def generate_user_uuid(self) -> UUID:
        """Generate new UUID4 for user."""
        stmt = """
        SELECT 1 FROM users WHERE uuid = :uuid
        UNION
        SELECT 1 FROM orphan_files WHERE owner_uuid = :uuid;
        """
        while True:
            uuid = uuid4()
            exists = await self.db.fetch_one(stmt, {'uuid': uuid})

            if not exists:
                return uuid

    async def create_user(
            self,
            raw_user: api_models.CreateUserIn,
            password: bytes,
    ) -> UUID:
        """Create user and return UUID."""
        stmt = sa.insert(
            models.User
        ).values(
            uuid=raw_user.uuid,
            login=raw_user.login,
            password=password.decode('utf-8'),
            name=raw_user.name,
        ).returning(
            models.User.uuid
        )
        return await self.db.execute(stmt)

    async def update_user(
            self,
            user: domain.User,
    ) -> UUID:
        """Update existing user."""
        stmt = sa.update(
            models.User
        ).values(
            login=user.login,
            password=user.password,
            name=user.name,
            root_item=str(user.root_item) if user.root_item else None,
        )
        return await self.db.execute(stmt)
