# -*- coding: utf-8 -*-
"""Search repository.
"""
import sqlalchemy as sa

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models

MAX_ITEMS_TO_RETURN = 1000


class SearchRepository(
    interfaces.AbsSearchRepository,
):
    """Repository that performs all search queries."""

    async def count_matching_anon(
            self,
            query: domain.Query,
            aim: domain.Aim,
    ) -> int:
        """Count matching items for unauthorised user."""
        public_users = sa.select(models.PublicUsers.user_uuid)

        stmt = sa.select(
            sa.func.count().label('total')
        ).select_from(
            models.ComputedTags
        ).join(
            models.Item,
            models.Item.uuid == models.ComputedTags.item_uuid,
            isouter=True,
        ).join(
            models.User,
            models.User.uuid == models.Item.owner_uuid,
        ).where(
            models.User.uuid.in_(public_users),
            models.ComputedTags.tags.contains(query.tags_include),
            ~models.ComputedTags.tags.overlap(query.tags_exclude)
        )

        if aim.nested:
            stmt = stmt.where(models.Item.is_collection == True)  # noqa

        response = await self.db.fetch_one(stmt)
        return int(response['total'])

    async def count_matching_known(
            self,
            user: domain.User,
            query: domain.Query,
            aim: domain.Aim,
    ) -> int:
        """Count available items for authorised user."""
        stmt = sa.select(
            sa.func.count().label('total')
        ).select_from(
            models.Item
        ).join(
            models.ComputedPermissions,
            models.Item.uuid == models.ComputedPermissions.item_uuid,
        ).join(
            models.ComputedTags,
            models.Item.uuid == models.ComputedTags.item_uuid,
        ).where(
            sa.or_(
                models.Item.owner_uuid == str(user.uuid),
                models.ComputedPermissions.permissions.any(str(user.uuid))
            ),
            models.ComputedPermissions.permissions != None,  # noqa
            models.ComputedTags.tags.contains(query.tags_include),
            ~models.ComputedTags.tags.overlap(query.tags_exclude)
        )

        if aim.nested:
            stmt = stmt.where(models.Item.is_collection == True)  # noqa

        response = await self.db.fetch_one(stmt)
        return int(response['total'])

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
