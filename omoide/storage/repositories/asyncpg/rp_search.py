# -*- coding: utf-8 -*-
"""Search repository.
"""
from omoide import domain
from omoide.domain import interfaces


class SearchRepository(
    interfaces.AbsSearchRepository,
):
    """Repository that performs all search queries."""

    async def total_matching_anon(
            self,
            query: domain.Query,
            aim: domain.Aim,
    ) -> int:
        """Count matching items for unauthorised user."""
        # TODO - rewrite to sqlalchemy
        _query = """
        SELECT count(*) AS total_items
        FROM items it
                 RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
          AND ct.tags @> :tags_include
          AND NOT ct.tags && :tags_exclude
        """

        if aim.nested:
            _query += '\nAND it.is_collection'

        values = {
            'tags_include': query.tags_include,
            'tags_exclude': query.tags_exclude,
        }

        _query += ';'
        response = await self.db.fetch_one(_query, values)
        return int(response['total_items'])

    async def total_matching_known(
            self,
            user: domain.User,
            query: domain.Query,
            aim: domain.Aim,
    ) -> int:
        """Count available items for authorised user."""
        # TODO - rewrite to sqlalchemy
        _query = """
        SELECT count(*) AS total_items
        FROM items it
                RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
                RIGHT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE (:user_uuid = ANY(cp.permissions)
               OR it.owner_uuid::text = :user_uuid)
          AND ct.tags @> :tags_include
          AND NOT ct.tags && :tags_exclude
        """

        if aim.nested:
            _query += '\nAND it.is_collection'

        values = {
            'user_uuid': str(user.uuid),
        }

        _query += ';'
        response = await self.db.fetch_one(_query, values)
        return int(response['total_items'])

    async def search_dynamic_anon(
            self,
            query: domain.Query,
            details: domain.Details,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items for unauthorised user."""
        # TODO - rewrite to sqlalchemy
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
                 RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
          AND it.number > :last_seen
          AND ct.tags @> :tags_include
          AND NOT ct.tags && :tags_exclude
        """

        if aim.nested:
            _query += '\nAND it.is_collection'

        values = {
            'limit': details.items_per_page,
            'tags_include': query.tags_include,
            'tags_exclude': query.tags_exclude,
            'last_seen': -1,
        }

        if aim.ordered:
            _query += '\nORDER BY number LIMIT :limit;'
            values['last_seen'] = aim.last_seen
        else:
            _query += '\nORDER BY random() LIMIT :limit;'

        response = await self.db.fetch_all(_query, values)
        return [domain.Item(**row) for row in response]

    async def search_dynamic_known(
            self,
            user: domain.User,
            query: domain.Query,
            details: domain.Details,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find specific items for authorised user."""
        # TODO - rewrite to sqlalchemy
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
                 LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE (:user_uuid = ANY(cp.permissions)
               OR it.owner_uuid::text = :user_uuid)
          AND it.number > :last_seen
          AND ct.tags @> :tags_include
          AND NOT ct.tags && :tags_exclude
        """

        if aim.nested:
            _query += '\nAND it.is_collection'

        values = {
            'user_uuid': str(user.uuid),
            'limit': details.items_per_page,
            'tags_include': query.tags_include,
            'tags_exclude': query.tags_exclude,
            'last_seen': -1,
        }

        if aim.ordered:
            _query += 'ORDER BY number LIMIT :limit;'
            values['last_seen'] = aim.last_seen
        else:
            _query += 'ORDER BY random() LIMIT :limit;'

        response = await self.db.fetch_all(_query, values)
        return [domain.Item(**row) for row in response]

    async def search_paged_anon(
            self,
            query: domain.Query,
            details: domain.Details,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items for unauthorised user."""
        # TODO - rewrite to sqlalchemy
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
                 RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
        WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
          AND ct.tags @> :tags_include
          AND NOT ct.tags && :tags_exclude
        """

        if aim.nested:
            _query += '\nAND it.is_collection'

        values = {
            'tags_include': query.tags_include,
            'tags_exclude': query.tags_exclude,
            'limit': details.items_per_page,
            'offset': details.offset,
        }

        if aim.ordered:
            _query += '\nORDER BY number LIMIT :limit OFFSET :offset;'
        else:
            _query += '\nORDER BY random() LIMIT :limit OFFSET :offset;'

        response = await self.db.fetch_all(_query, values)
        return [domain.Item(**row) for row in response]

    async def search_paged_known(
            self,
            user: domain.User,
            query: domain.Query,
            details: domain.Details,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items for authorised user."""
        # TODO - rewrite to sqlalchemy
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
                 LEFT JOIN computed_permissions cp ON cp.item_uuid = it.uuid
        WHERE (:user_uuid = ANY(cp.permissions)
               OR it.owner_uuid::text = :user_uuid)
          AND ct.tags @> :tags_include
          AND NOT ct.tags && :tags_exclude
        """

        if aim.nested:
            _query += '\nAND it.is_collection'

        values = {
            'user_uuid': str(user.uuid),
            'limit': details.items_per_page,
            'tags_include': query.tags_include,
            'tags_exclude': query.tags_exclude,
            'offset': details.offset,
        }

        if aim.ordered:
            _query += 'ORDER BY number LIMIT :limit OFFSET :offset;'
        else:
            _query += 'ORDER BY random() LIMIT :limit OFFSET :offset;'

        response = await self.db.fetch_all(_query, values)
        return [domain.Item(**row) for row in response]
