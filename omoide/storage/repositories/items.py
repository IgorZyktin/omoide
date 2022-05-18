# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on items and their data.
"""
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces import repositories as repo_interfaces
from omoide.storage import repositories as repo_implementations


class ItemsRepository(
    repo_implementations.BaseRepository,
    repo_interfaces.AbsItemsRepository,
):
    """Repository that perform CRUD operations on items and their data."""

    async def get_item(
            self,
            uuid: UUID,
    ) -> Optional[domain.Item]:
        """Return item or None."""
        stmt = """
        SELECT uuid,
               parent_uuid,
               owner_uuid,
               number,
               name,
               is_collection,
               content_ext,
               preview_ext,
               thumbnail_ext
        FROM items
        WHERE uuid = :uuid;
        """

        response = await self.db.fetch_one(stmt, {'uuid': uuid})
        return domain.Item.from_map(response) if response else None

    async def delete_item(
            self,
            uuid: UUID,
    ) -> None:
        """Delete item with given UUID."""
        stmt = """DELETE FROM items WHERE uuid = :uuid;"""
        await self.db.execute(stmt, {'uuid': uuid})
