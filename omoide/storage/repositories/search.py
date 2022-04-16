# -*- coding: utf-8 -*-
"""Search repository.
"""
from omoide import domain
from omoide.domain import interfaces
from omoide.storage.repositories import base


class SearchRepository(
    base.BaseRepository,
    interfaces.AbsSearchRepository,
):
    """Repository that performs all search queries."""

    async def total_random_anon(self) -> int:
        """Count all available items for unauthorised user."""
        query = """
        SELECT count(*) AS total_items
        FROM items
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users);
        """

        response = await self.db.fetch_one(query)
        return int(response['total_items'])

    async def total_specific_anon(self, query: domain.Query) -> int:
        """Count available items for unauthorised user."""
        _query = """
        SELECT count(*) AS total_items
        FROM items it
                 RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
          AND ct.tags @> :tags_include
          AND NOT ct.tags && :tags_exclude;
        """

        values = {
            'tags_include': query.tags_include,
            'tags_exclude': query.tags_exclude,
        }

        response = await self.db.fetch_one(_query, values)
        return int(response['total_items'])

    async def search_random_anon(
            self,
            query: domain.Query,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Find random items for unauthorised user."""
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
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
        ORDER BY random() LIMIT :limit OFFSET :offset;
        """

        values = {
            'limit': details.items_per_page,
            'offset': details.offset,
        }

        response = await self.db.fetch_all(_query, values)
        return [domain.Item.from_map(row) for row in response]

    async def search_specific_anon(
            self,
            query: domain.Query,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Find specific items for unauthorised user."""
        _query = """
        SELECT uuid,
               parent_uuid,
               owner_uuid,
               number,
               name,
               is_collection,
               content_ext,
               preview_ext,
               thumbnail_ext,
               ct.tags
        FROM items it
                 RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
          AND ct.tags @> :tags_include
          AND NOT ct.tags && :tags_exclude
        ORDER BY number LIMIT :limit OFFSET :offset;
        """

        values = {
            'limit': details.items_per_page,
            'offset': details.offset,
            'tags_include': query.tags_include,
            'tags_exclude': query.tags_exclude,
        }

        response = await self.db.fetch_all(_query, values)
        return [domain.Item.from_map(row) for row in response]

    async def total_random_known(
            self,
            user: domain.User,
    ) -> int:
        """Count all available items for authorised user."""
        query = """
        SELECT count(*) AS total_items
        FROM items it
                RIGHT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE :user_uuid = ANY(cp.permissions);
        """

        values = {
            'user_uuid': user.uuid,
        }

        response = await self.db.fetch_one(query, values)
        return int(response['total_items'])

    async def total_specific_known(
            self,
            user: domain.User,
            query: domain.Query,
    ) -> int:
        """Count available items for authorised user."""
        query = """
        SELECT count(*) AS total_items
        FROM items it
                RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
                RIGHT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE :user_uuid = ANY(cp.permissions)
          AND ct.tags @> :tags_include
          AND NOT ct.tags && :tags_exclude;
        """

        values = {
            'user_uuid': user.uuid,
        }

        response = await self.db.fetch_one(query, values)
        return int(response['total_items'])

    async def search_random_known(
            self,
            user: domain.User,
            query: domain.Query,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Find random items for authorised user."""
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
            RIGHT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE :user_uuid = ANY(cp.permissions)
        ORDER BY random() LIMIT :limit OFFSET :offset;
        """

        values = {
            'user_uuid': user.uuid,
            'limit': details.items_per_page,
            'offset': details.offset,
        }

        response = await self.db.fetch_all(_query, values)
        return [domain.Item.from_map(row) for row in response]

    async def search_specific_known(
            self,
            user: domain.User,
            query: domain.Query,
            details: domain.Details,
    ) -> list[domain.Item]:
        """Find specific items for authorised user."""
        _query = """
        SELECT uuid,
               parent_uuid,
               owner_uuid,
               number,
               name,
               is_collection,
               content_ext,
               preview_ext,
               thumbnail_ext,
               ct.tags
        FROM items it
                 RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
                 RIGHT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE :user_uuid = ANY(cp.permissions)
          AND ct.tags @> :tags_include
          AND NOT ct.tags && :tags_exclude
        ORDER BY number LIMIT :limit OFFSET :offset;
        """

        values = {
            'user_uuid': user.uuid,
            'limit': details.items_per_page,
            'offset': details.offset,
            'tags_include': query.tags_include,
            'tags_exclude': query.tags_exclude,
        }

        response = await self.db.fetch_all(_query, values)
        return [domain.Item.from_map(row) for row in response]
