"""Search repository.
"""
import sqlalchemy as sa
from sqlalchemy.sql import Select

from omoide import domain
from omoide.domain import interfaces
from omoide.domain.core import core_models
from omoide.infra import custom_logging
from omoide.storage.database import models
from omoide.storage.repositories.asyncpg import queries

LOG = custom_logging.get_logger(__name__)


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

        stmt = queries.ensure_user_has_permissions(user, stmt)

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

    async def count_all_tags(
            self,
            user: domain.User,
    ) -> list[tuple[str, int]]:
        """Return statistics for known tags."""
        if user.is_anon:
            stmt = sa.select(
                models.KnownTagsAnon.tag,
                models.KnownTagsAnon.counter,
            ).order_by(
                sa.desc(models.KnownTagsAnon.counter),
            )

        else:
            stmt = sa.select(
                models.KnownTags.tag,
                models.KnownTags.counter,
            ).where(
                models.KnownTags.user_uuid == user.uuid,
            ).order_by(
                sa.desc(models.KnownTags.counter),
            )

        response = await self.db.fetch_all(stmt)
        # TODO - return dict from this method
        return [(x['tag'], x['counter']) for x in response]

    async def count_all_tags_anon(self) -> dict[str, int]:
        """Return statistics for used tags."""
        stmt = sa.select(
            models.KnownTagsAnon.tag,
            models.KnownTagsAnon.counter,
        ).order_by(
            sa.desc(models.KnownTagsAnon.counter),
        )

        response = await self.db.fetch_all(stmt)
        return {x['tag']: x['counter'] for x in response}

    async def guess_tag_known(
            self,
            user: core_models.User,
            user_input: str,
            limit: int,
    ) -> list[core_models.GuessResult]:
        """Guess tag for known user."""
        stmt = sa.select(
            models.KnownTags.tag,
            models.KnownTags.counter,
        ).where(
            models.KnownTags.tag.ilike(user_input + '%'),  # type: ignore
            models.KnownTags.user_uuid == user.uuid,
        ).order_by(
            sa.desc(models.KnownTags.counter),
        ).limit(limit)

        response = await self.db.fetch_all(stmt)

        return [core_models.GuessResult(**x) for x in response]

    async def guess_tag_anon(
            self,
            user: core_models.User,
            user_input: str,
            limit: int,
    ) -> list[core_models.GuessResult]:
        """Guess tag for anon user."""
        stmt = sa.select(
            models.KnownTagsAnon.tag,
            models.KnownTagsAnon.counter,
        ).where(
            models.KnownTagsAnon.tag.ilike(user_input + '%'),  # type: ignore
        ).order_by(
            sa.desc(models.KnownTagsAnon.counter),
        ).limit(limit)

        response = await self.db.fetch_all(stmt)

        return [core_models.GuessResult(**x) for x in response]
