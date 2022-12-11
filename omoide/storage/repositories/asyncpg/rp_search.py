# -*- coding: utf-8 -*-
"""Search repository.
"""
from typing import Optional
from typing import Type

import sqlalchemy as sa
from sqlalchemy.sql import Select

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models
from omoide.storage.repositories.asyncpg import queries


class SearchRepository(
    interfaces.AbsSearchRepository,
):
    """Repository that performs all search queries."""

    @staticmethod
    def _expand_query(
            user: domain.User,
            aim: domain.Aim,
            stmt: Select,
    ) -> Select:
        """Add access control and filtering."""
        stmt = stmt.join(
            models.ComputedTags,
            models.ComputedTags.item_uuid == models.Item.uuid,
        )

        if user.is_anon():
            stmt = stmt.join(
                models.User,
                models.User.uuid == models.Item.owner_uuid,
            ).where(
                models.User.uuid.in_(queries.public_user_uuids())  # noqa
            )
        else:
            stmt = stmt.join(
                models.ComputedPermissions,
                models.ComputedPermissions.item_uuid == models.Item.uuid,
            ).where(
                sa.or_(
                    models.Item.owner_uuid == user.uuid,
                    models.ComputedPermissions.permissions.any(str(user.uuid))
                ),
            )

        stmt = stmt.where(
            models.ComputedTags.tags.contains(aim.query.tags_include),
            ~models.ComputedTags.tags.overlap(aim.query.tags_exclude),
        )

        if aim.nested:
            stmt = stmt.where(models.Item.is_collection == True)  # noqa

        return stmt

    @staticmethod
    def _maybe_trim(
            stmt: Select,
            aim: domain.Aim,
    ) -> Select:
        """Limit query if user demands it."""
        if aim.ordered:
            stmt = stmt.where(
                models.Item.number > aim.last_seen,
            ).order_by(
                models.Item.number,
            )
        else:
            stmt = stmt.order_by(sa.func.random())

        return stmt

    async def count_matching_items(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> int:
        """Count matching items for search query."""
        stmt = sa.select(
            sa.func.count().label('total_items')
        ).select_from(
            models.Item
        )

        stmt = self._expand_query(user, aim, stmt)

        response = await self.db.fetch_one(stmt)
        return int(response['total_items'])

    async def get_matching_items(
            self,
            user: domain.User,
            aim: domain.Aim,
            limit: int,
    ) -> list[domain.Item]:
        """Find items for dynamic load."""
        stmt = sa.select(
            models.Item
        )

        stmt = self._expand_query(user, aim, stmt)
        stmt = self._maybe_trim(stmt, aim)

        if aim.paged:
            stmt = stmt.offset(aim.offset)

        stmt = stmt.limit(min(aim.items_per_page, limit))
        response = await self.db.fetch_all(stmt)
        return [domain.Item(**row) for row in response]

    async def guess_tag_anon(
            self,
            text: str,
            limit: int,
    ) -> list[str]:
        """Guess tag for anon user."""
        return await self._guess_generic(
            models.KnownTagsAnon, None, text, limit)

    async def guess_tag_known(
            self,
            user: domain.User,
            text: str,
            limit: int,
    ) -> list[str]:
        """Guess tag for known user."""
        return await self._guess_generic(
            models.KnownTags, user, text, limit)

    async def _guess_generic(
            self,
            model: Type[models.KnownTagsAnon] | Type[models.KnownTags],
            user: Optional[domain.User],
            text: str,
            limit: int,
    ) -> list[str]:
        """Generic tags getter."""
        stmt = sa.select(
            model.tag
        ).where(
            model.tag.ilike(text + '%')  # type: ignore
        )

        if user is None:
            assert issubclass(model, models.KnownTagsAnon)
        else:
            assert issubclass(model, models.KnownTags)
            stmt = stmt.where(
                models.KnownTags.user_uuid == user.uuid,
            )

        stmt = stmt.order_by(sa.desc(model.counter)).limit(limit)
        response = await self.db.fetch_all(stmt)
        return [x['tag'] for x in response]
