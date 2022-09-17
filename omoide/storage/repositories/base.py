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
        return domain.User.from_map(response) if response else None

    async def get_user_by_login(
            self,
            user_login: str,
    ) -> Optional[domain.User]:
        """Return user or None."""
        query = """
        SELECT *
        FROM users
        WHERE login = :user_login;
        """

        response = await self.db.fetch_one(query, {'user_login': user_login})
        return domain.User.from_map(response) if response else None

    async def read_item(
            self,
            uuid: UUID,
    ) -> Optional[domain.Item]:
        """Return item or None."""
        stmt = sqlalchemy.select(models.Item).where(models.Item.uuid == uuid)
        response = await self.db.fetch_one(stmt)
        return domain.Item.from_map(response) if response else None

    async def get_item_with_position(
            self,
            user: domain.User,
            item_uuid: UUID,
            child_uuid: UUID,
            details: domain.Details,
    ) -> Optional[domain.PositionedItem]:
        """Return item with its position in siblings."""
        if user.is_anon():
            query = """
            WITH children AS (
                SELECT uuid
                FROM items
                WHERE parent_uuid = :item_uuid
                ORDER BY number
            )
            SELECT uuid,
                   parent_uuid,
                   owner_uuid,
                   number,
                   name,
                   is_collection,
                   content_ext,
                   preview_ext,
                   thumbnail_ext,
                   tags,
                   (select array_position(array(select uuid from children),
                                          :child_uuid)) as position,
                   (select count(*) from children) as total_items
            FROM items
            WHERE uuid = :item_uuid;
            """
            values = {
                'item_uuid': str(item_uuid),
                'child_uuid': str(child_uuid),
            }
        else:
            query = """
            WITH children AS (
                SELECT uuid
                FROM items it
                RIGHT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
                WHERE parent_uuid = :item_uuid
                AND (:user_uuid = ANY(cp.permissions)
                 OR it.owner_uuid::text = :user_uuid)
                ORDER BY number
            )
            SELECT uuid,
                   parent_uuid,
                   owner_uuid,
                   number,
                   name,
                   is_collection,
                   content_ext,
                   preview_ext,
                   thumbnail_ext,
                   tags,
                   (select array_position(array(select uuid from children),
                                          :child_uuid)) as position,
                   (select count(*) from children) as total_items
            FROM items
            WHERE uuid = :item_uuid;
            """

            values = {
                'user_uuid': str(user.uuid),
                'item_uuid': str(item_uuid),
                'child_uuid': str(child_uuid),
            }

        response = await self.db.fetch_one(query, values)

        if response is None:
            return None

        mapping = dict(response)

        return domain.PositionedItem(
            position=mapping.pop('position') or 1,
            total_items=mapping.pop('total_items') or 1,
            items_per_page=details.items_per_page,
            item=domain.Item.from_map(mapping),
        )
