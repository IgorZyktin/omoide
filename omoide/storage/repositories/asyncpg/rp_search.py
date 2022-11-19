# -*- coding: utf-8 -*-
"""Search repository.
"""
import sqlalchemy as sa
from sqlalchemy.sql.selectable import Select

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
            aim: domain.Aim,
    ) -> int:
        """Count matching items for unauthorised user."""
        stmt = sa.select(
            sa.func.count().label('total')
        ).select_from(
            models.ComputedTags
        ).join(
            models.Item,
            models.Item.uuid == models.ComputedTags.item_uuid,
        ).join(
            models.User,
            models.User.uuid == models.Item.owner_uuid,
        ).where(
            models.User.uuid.in_(self._get_public_users()),
            models.ComputedTags.tags.contains(aim.query.tags_include),
            ~models.ComputedTags.tags.overlap(aim.query.tags_exclude)
        )

        if aim.nested:
            stmt = stmt.where(models.Item.is_collection == True)  # noqa

        response = await self.db.fetch_one(stmt)
        return int(response['total'])

    async def count_matching_known(
            self,
            user: domain.User,
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
            models.ComputedTags.tags.contains(aim.query.tags_include),
            ~models.ComputedTags.tags.overlap(aim.query.tags_exclude)
        )

        if aim.nested:
            stmt = stmt.where(models.Item.is_collection == True)  # noqa

        response = await self.db.fetch_one(stmt)
        return int(response['total'])

    def _search_anon(
            self,
            query: domain.Query,
    ) -> Select:
        """Shorthand for anon user."""
        stmt = sa.select(
            models.Item
        ).join(
            models.ComputedTags,
            models.ComputedTags.item_uuid == models.Item.uuid,
        ).join(
            models.User,
            models.User.uuid == models.Item.owner_uuid,
        ).where(
            models.User.uuid.in_(self._get_public_users()),
            models.ComputedTags.tags.contains(query.tags_include),
            ~models.ComputedTags.tags.overlap(query.tags_exclude)
        )
        return stmt

    @staticmethod
    def _get_public_users() -> Select:
        """Shorthand for public user selection."""
        return sa.select(models.PublicUsers.user_uuid)

    @staticmethod
    def _maybe_trim(
            stmt: Select,
            aim: domain.Aim,
    ) -> Select:
        """Limit query if user demands it."""
        if aim.nested:
            stmt = stmt.where(models.Item.is_collection == True)  # noqa

        if aim.ordered:
            stmt = stmt.where(
                models.Item.number > aim.last_seen,
            ).order_by(
                models.Item.number,
            )
        else:
            stmt = stmt.order_by(sa.func.random())

        return stmt

    @staticmethod
    def _search_known(
            user: domain.User,
            query: domain.Query,
    ) -> Select:
        """Shorthand for known user."""
        stmt = sa.select(
            models.Item
        ).join(
            models.ComputedTags,
            models.ComputedTags.item_uuid == models.Item.uuid,
        ).join(
            models.ComputedPermissions,
            models.ComputedPermissions.item_uuid == models.Item.uuid,
        ).where(
            sa.or_(
                models.Item.owner_uuid == str(user.uuid),
                models.ComputedPermissions.permissions.any(str(user.uuid))
            ),
            models.ComputedTags.tags.contains(query.tags_include),
            ~models.ComputedTags.tags.overlap(query.tags_exclude)
        )
        return stmt

    async def search_dynamic_anon(
            self,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items for unauthorised user."""
        stmt = self._search_anon(aim.query)
        stmt = self._maybe_trim(stmt, aim)
        stmt = stmt.limit(min(aim.items_per_page, MAX_ITEMS_TO_RETURN))
        response = await self.db.fetch_all(stmt)
        return [domain.Item(**row) for row in response]

    async def search_dynamic_known(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find specific items for authorised user."""
        stmt = self._search_known(user, aim.query)
        stmt = self._maybe_trim(stmt, aim)
        stmt = stmt.limit(min(aim.items_per_page, MAX_ITEMS_TO_RETURN))
        response = await self.db.fetch_all(stmt)
        return [domain.Item(**row) for row in response]

    async def search_paged_anon(
            self,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items for unauthorised user."""
        stmt = self._search_anon(aim.query)
        stmt = self._maybe_trim(stmt, aim)
        stmt = stmt.offset(aim.offset)
        stmt = stmt.limit(min(aim.items_per_page, MAX_ITEMS_TO_RETURN))
        response = await self.db.fetch_all(stmt)
        return [domain.Item(**row) for row in response]

    async def search_paged_known(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find items for authorised user."""
        stmt = self._search_known(user, aim.query)
        stmt = self._maybe_trim(stmt, aim)
        stmt = stmt.offset(aim.offset)
        stmt = stmt.limit(min(aim.items_per_page, MAX_ITEMS_TO_RETURN))
        response = await self.db.fetch_all(stmt)
        return [domain.Item(**row) for row in response]
