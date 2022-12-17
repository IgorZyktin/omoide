# -*- coding: utf-8 -*-
"""Search repository.
"""
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
            obligation: domain.Obligation,
    ) -> list[domain.Item]:
        """Find items for dynamic load."""
        stmt = sa.select(
            models.Item
        )

        stmt = self._expand_query(user, aim, stmt)
        stmt = self._maybe_trim(stmt, aim)

        if aim.paged:
            stmt = stmt.offset(aim.offset)

        stmt = stmt.limit(
            min(aim.items_per_page, obligation.max_results),
        )

        response = await self.db.fetch_all(stmt)
        return [domain.Item(**row) for row in response]

    async def guess_tag_known(
            self,
            user: domain.User,
            guess: domain.GuessTag,
            obligation: domain.Obligation,
    ) -> list[domain.GuessResult]:
        """Guess tag for known user."""
        assert user.is_registered

        stmt = sa.select(
            models.KnownTags.tag,
            models.KnownTags.counter,
        ).where(
            models.KnownTags.tag.ilike(guess.text + '%'),  # type: ignore
            models.KnownTags.user_uuid == user.uuid,
        ).order_by(
            sa.desc(models.KnownTags.counter),
        ).limit(
            obligation.max_results,
        )

        response = await self.db.fetch_all(stmt)
        return [domain.GuessResult(**x) for x in response]

    async def guess_tag_anon(
            self,
            user: domain.User,
            guess: domain.GuessTag,
            obligation: domain.Obligation,
    ) -> list[domain.GuessResult]:
        """Guess tag for anon user."""
        assert user.is_not_registered

        stmt = sa.select(
            models.KnownTagsAnon.tag,
            models.KnownTagsAnon.counter,
        ).where(
            models.KnownTagsAnon.tag.ilike(guess.text + '%'),  # type: ignore
        ).order_by(
            sa.desc(models.KnownTagsAnon.counter),
        ).limit(
            obligation.max_results,
        )

        response = await self.db.fetch_all(stmt)
        return [domain.GuessResult(**x) for x in response]

    async def count_all_tags(
            self,
            user: domain.User,
    ) -> list[tuple[str, int]]:
        """Return statistics for known tags."""
        # FIXME
        return []
