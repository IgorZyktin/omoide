# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on users and their data.
"""
from typing import Optional
from uuid import UUID
from uuid import uuid4

import sqlalchemy

from omoide import domain
from omoide.domain.interfaces import repositories as repo_interfaces
from omoide.presentation import api_models
from omoide.storage.database import models


class UsersRepository(repo_interfaces.AbsUsersRepository):
    """Repository that perform CRUD operations on users and their data."""

    async def generate_user_uuid(self) -> UUID:
        """Generate new UUID4 for user."""
        stmt = """
        SELECT 1 FROM users WHERE uuid = :uuid;
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
        stmt = """
        INSERT INTO users (
            uuid,
            login,
            password,
            name,
            root_item
        ) VALUES (
            :uuid,
            :login,
            :password,
            :name,
            NULL
        )
        RETURNING uuid;
        """

        values = {
            'uuid': raw_user.uuid,
            'login': raw_user.login,
            'password': password.decode('utf-8'),
            'name': raw_user.name,
        }

        return await self.db.execute(stmt, values)

    async def read_user(
            self,
            uuid: UUID,
    ) -> Optional[domain.User]:
        """Return user or None."""
        stmt = sqlalchemy.select(models.User).where(models.User.uuid == uuid)
        response = await self.db.fetch_one(stmt)
        return domain.User.from_map(dict(response)) if response else None

    async def read_all_users(
            self,
            uuids: list[UUID | str],
    ) -> list[domain.User]:
        """Return list of users with given uuids."""
        stmt = sqlalchemy.select(
            models.User
        ).where(
            models.User.uuid.in_(tuple(uuids))  # noqa
        )

        response = await self.db.fetch_all(stmt)

        return [
            domain.User.from_map(dict(record))
            for record in response
        ]

    async def update_user(
            self,
            user: domain.User,
    ) -> UUID:
        """Update existing user."""
        stmt = """
        UPDATE users SET
            login = :login,
            password = :password,
            name = :name,
            root_item = :root_item
        WHERE uuid = :uuid;
        """

        values = {
            'uuid': user.uuid,
            'login': user.login,
            'password': user.password,
            'name': user.name,
            'root_item': user.root_item,
        }

        return await self.db.execute(stmt, values)
