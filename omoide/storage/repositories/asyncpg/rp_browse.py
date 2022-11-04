# -*- coding: utf-8 -*-
"""Browse repository.
"""
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces
from omoide.domain.interfaces.in_storage \
    .in_repositories.in_rp_browse import AbsBrowseRepository
from omoide.storage.repositories.asyncpg \
    .rp_items_read import ItemsReadRepository


class BrowseRepository(
    AbsBrowseRepository,
    ItemsReadRepository,
):
    """Repository that performs all browse queries."""

    async def get_children(
            self,
            uuid: UUID,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Load all children and sub children of the record."""
        _query = """
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
        WHERE parent_uuid = :uuid
        AND uuid <> :uuid
        ORDER BY number
        LIMIT :limit OFFSET :offset;
        """

        values = {
            'uuid': str(uuid),
            'limit': details.items_per_page,
            'offset': details.offset,
        }

        response = await self.db.fetch_all(_query, values)
        return [domain.Item(**x) for x in response]

    async def count_items(
            self,
            uuid: UUID,
    ) -> int:
        """Count all children with all required fields."""
        query = """
        SELECT count(*) AS total_items
        FROM items
        WHERE parent_uuid = :uuid;
        """

        response = await self.db.fetch_one(query, {'uuid': str(uuid)})
        return int(response['total_items'])

    async def get_specific_children(
            self,
            user: domain.User,
            uuid: UUID,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Load all children with all required fields (and access)."""
        _query = """
        SELECT uuid,
               parent_uuid,
               owner_uuid,
               number,
               name,
               is_collection,
               content_ext,
               preview_ext,
               thumbnail_ext
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE parent_uuid = :item_uuid
            AND uuid <> :item_uuid
            AND (:user_uuid = ANY(cp.permissions)
                 OR it.owner_uuid::text = :user_uuid)
        ORDER BY number
        LIMIT :limit OFFSET :offset;
        """

        values = {
            'user_uuid': str(user.uuid),
            'item_uuid': str(uuid),
            'limit': details.items_per_page,
            'offset': details.offset,
        }

        response = await self.db.fetch_all(_query, values)
        return [domain.Item(**x) for x in response]

    async def count_specific_items(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> int:
        """Count all children with all required fields (and access)."""
        query = """
        SELECT count(*) AS total_items
        FROM items it
            LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE parent_uuid = :item_uuid
            AND (:user_uuid = ANY(cp.permissions)
                 OR it.owner_uuid::text = :user_uuid);
        """

        values = {
            'user_uuid': str(user.uuid),
            'item_uuid': str(uuid),
        }

        response = await self.db.fetch_one(query, values)
        return int(response['total_items'])

    async def get_simple_location(
            self,
            user: domain.User,
            owner: domain.User,
            item: domain.Item,
    ) -> Optional[domain.SimpleLocation]:
        """Return Location of the item (without pagination)."""
        ancestors = await self.get_simple_ancestors(item)
        return domain.SimpleLocation(items=ancestors + [item])

    async def get_simple_ancestors(
            self,
            item: domain.Item,
    ) -> list[domain.Item]:
        """Return list of ancestors for given item."""
        # TODO(i.zyktin): what if user has no access
        #  to the item in the middle of dependence chain?

        ancestors = []
        item_uuid = item.parent_uuid

        while True:
            if item_uuid is None:
                break

            ancestor = await self.read_item(item_uuid)

            if ancestor is None:
                break

            ancestors.append(ancestor)
            item_uuid = ancestor.parent_uuid

        ancestors.reverse()
        return ancestors

    async def get_location(
            self,
            user: domain.User,
            uuid: UUID,
            details: domain.Details,
            users_repo: interfaces.AbsUsersReadRepository,
    ) -> Optional[domain.Location]:
        """Return Location of the item."""
        current_item = await self.read_item(uuid)

        if current_item is None:
            return None

        owner = await users_repo.read_user(current_item.owner_uuid)

        if owner is None:
            return None

        ancestors = await self.get_complex_ancestors(
            user=user,
            item=current_item,
            details=details,
        )

        return domain.Location(
            owner=owner,
            items=ancestors,
            current_item=current_item,
        )

    async def get_complex_ancestors(
            self,
            user: domain.User,
            item: domain.Item,
            details: domain.Details,
    ) -> list[domain.PositionedItem]:
        """Return list of positioned ancestors of given item."""
        ancestors = []

        item_uuid = item.parent_uuid
        child_uuid = item.uuid

        while True:
            if item_uuid is None:
                break

            ancestor = await self.get_item_with_position(
                user=user,
                item_uuid=item_uuid,
                child_uuid=child_uuid,
                details=details,
            )

            if ancestor is None:
                break

            ancestors.append(ancestor)
            item_uuid = ancestor.item.parent_uuid
            child_uuid = ancestor.item.uuid

        ancestors.reverse()
        return ancestors

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
