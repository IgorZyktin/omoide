# -*- coding: utf-8 -*-
"""Base functionality for all concrete repositories.
"""
from typing import Optional
from uuid import UUID, uuid4

import sqlalchemy

from omoide import domain
from omoide.storage.database import models
from omoide.storage.repositories import base_logic


class BaseRepository(base_logic.BaseRepositoryLogic):
    """Base functionality for all concrete repositories."""

    async def generate_uuid(self) -> UUID:
        """Generate new UUID4."""
        query = """
        SELECT 1 FROM items WHERE uuid = :uuid;
        """
        while True:
            new_uuid = uuid4()
            exists = await self.db.fetch_one(query, {'uuid': new_uuid})

            if not exists:
                return new_uuid

    async def user_is_public(
            self,
            owner_uuid: str,
    ) -> bool:
        """Return True if owner is a public user."""
        query = """
        SELECT 1
        FROM public_users
        WHERE user_uuid = :user_uuid;
        """
        response = await self.db.fetch_one(query, {'user_uuid': owner_uuid})
        return response is not None

    async def get_user(
            self,
            user_uuid: UUID,
    ) -> Optional[domain.User]:
        """Return user or None."""
        query = """
        SELECT *
        FROM users
        WHERE uuid = :user_uuid;
        """

        response = await self.db.fetch_one(query,
                                           {'user_uuid': str(user_uuid)})
        return domain.User(**response) if response else None

    async def read_item(
            self,
            uuid: UUID,
    ) -> Optional[domain.Item]:
        """Return item or None."""
        stmt = sqlalchemy.select(models.Item).where(models.Item.uuid == uuid)
        response = await self.db.fetch_one(stmt)
        return domain.Item.from_map(response) if response else None

