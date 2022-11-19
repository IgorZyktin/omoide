# -*- coding: utf-8 -*-
"""Repository that performs read operations on users.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models


class UsersReadRepository(interfaces.AbsUsersReadRepository):
    """Repository that performs read operations on users."""

    async def read_user(
            self,
            uuid: UUID,
    ) -> Optional[domain.User]:
        """Return User or None."""
        stmt = sa.select(
            models.User
        ).where(
            models.User.uuid == uuid
        )
        response = await self.db.fetch_one(stmt)
        return domain.User(**response) if response else None

    async def read_user_by_login(
            self,
            login: str,
    ) -> Optional[domain.User]:
        """Return User or None."""
        stmt = sa.select(
            models.User
        ).where(
            models.User.login == login
        )
        response = await self.db.fetch_one(stmt)
        return domain.User(**response) if response else None

    async def read_all_users(
            self,
            uuids: list[UUID],
    ) -> list[domain.User]:
        """Return list of users with given uuids."""
        stmt = sa.select(
            models.User
        ).where(
            models.User.uuid.in_(tuple(str(x) for x in uuids))  # noqa
        )
        response = await self.db.fetch_all(stmt)
        return [domain.User(**record) for record in response]
