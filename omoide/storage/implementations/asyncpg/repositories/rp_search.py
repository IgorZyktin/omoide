"""Search repository."""
import abc
from typing import Literal

import sqlalchemy as sa
from sqlalchemy.sql import Select

from omoide import models
from omoide.storage import interfaces as storage_interfaces
from omoide.storage.database import db_models
from omoide.storage.implementations import asyncpg
from omoide.storage.implementations.asyncpg.repositories import queries


class _SearchRepositoryBase(
    storage_interfaces.AbsSearchRepository,
    asyncpg.AsyncpgStorage,
    abc.ABC,
):
    """Base class with helper methods."""

    @staticmethod
    def _expand_query(
        user: models.User,
        stmt: Select,
        tags_include: set[str],
        tags_exclude: set[str],
        only_collections: bool,
    ) -> Select:
        """Add access control and filtering."""
        stmt = stmt.join(
            db_models.ComputedTags,
            db_models.ComputedTags.item_uuid == db_models.Item.uuid,
        )

        stmt = queries.ensure_user_has_permissions(user, stmt)

        stmt = stmt.where(
            db_models.ComputedTags.tags.contains(tuple(tags_include)),
            ~db_models.ComputedTags.tags.overlap(tuple(tags_exclude)),
        )

        if only_collections:
            stmt = stmt.where(db_models.Item.is_collection == True)  # noqa

        return stmt

    @staticmethod
    def _apply_ordering(
        stmt: Select,
        ordering: Literal['asc', 'desc', 'random'],
        last_seen: int,
    ) -> Select:
        """Limit query if user demands it."""
        if ordering != 'random' and last_seen >= 0:
            stmt = stmt.where(db_models.Item.number > last_seen)

        if ordering == 'asc':
            stmt = stmt.order_by(db_models.Item.number)
        elif ordering == 'desc':
            stmt = stmt.order_by(sa.desc(db_models.Item.number))
        else:
            stmt = stmt.order_by(sa.func.random())

        return stmt


class SearchRepository(_SearchRepositoryBase):
    """Repository that performs all search queries."""

    async def count(
        self,
        user: models.User,
        tags_include: set[str],
        tags_exclude: set[str],
        only_collections: bool,
    ) -> int:
        """Return total amount of items relevant to this search query."""
        stmt = sa.select(
            sa.func.count().label('total_items')
        ).select_from(
            db_models.Item
        )

        stmt = self._expand_query(
            user=user,
            stmt=stmt,
            tags_include=tags_include,
            tags_exclude=tags_exclude,
            only_collections=only_collections,
        )

        response = await self.db.fetch_one(stmt)

        return int(response['total_items'])

    async def search(
        self,
        user: models.User,
        tags_include: set[str],
        tags_exclude: set[str],
        only_collections: bool,
        ordering: Literal['asc', 'desc', 'random'],
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Find items for dynamic load."""
        stmt = sa.select(db_models.Item)

        stmt = self._expand_query(
            user=user,
            stmt=stmt,
            tags_include=tags_include,
            tags_exclude=tags_exclude,
            only_collections=only_collections,
        )

        stmt = self._apply_ordering(
            stmt=stmt,
            ordering=ordering,
            last_seen=last_seen,
        )

        stmt = stmt.limit(limit)

        response = await self.db.fetch_all(stmt)

        return [models.Item(**row) for row in response]

    async def count_all_tags_anon(self) -> dict[str, int]:
        """Return counters for known tags (anon user)."""
        stmt = sa.select(
            db_models.KnownTagsAnon.tag,
            db_models.KnownTagsAnon.counter,
        ).order_by(
            sa.desc(db_models.KnownTagsAnon.counter),
        )

        response = await self.db.fetch_all(stmt)

        return {x['tag']: x['counter'] for x in response}

    async def count_all_tags_known(self, user: models.User) -> dict[str, int]:
        """Return counters for known tags (known user)."""
        stmt = sa.select(
            db_models.KnownTags.tag,
            db_models.KnownTags.counter,
        ).where(
            db_models.KnownTags.user_uuid == user.uuid,
        ).order_by(
            sa.desc(db_models.KnownTags.counter),
        )

        response = await self.db.fetch_all(stmt)

        return {x['tag']: x['counter'] for x in response}

    async def autocomplete_tag_anon(self, tag: str, limit: int) -> list[str]:
        """Autocomplete tag for anon user."""
        stmt = sa.select(
            db_models.KnownTagsAnon.tag
        ).where(
            db_models.KnownTagsAnon.tag.ilike(tag + '%'),  # type: ignore
            db_models.KnownTagsAnon.counter > 0,
        ).order_by(
            sa.desc(db_models.KnownTagsAnon.counter),
            sa.asc(db_models.KnownTagsAnon.tag),
        ).limit(limit)

        response = await self.db.fetch_all(stmt)

        return [x.tag for x in response]

    async def autocomplete_tag_known(
        self,
        user: models.User,
        tag: str,
        limit: int,
    ) -> list[str]:
        """Autocomplete tag for known user."""
        stmt = sa.select(
            db_models.KnownTags.tag,
        ).where(
            db_models.KnownTags.tag.ilike(tag + '%'),  # type: ignore
            db_models.KnownTags.user_uuid == user.uuid,
            db_models.KnownTags.counter > 0,
        ).order_by(
            sa.desc(db_models.KnownTags.counter),
            sa.asc(db_models.KnownTags.tag),
        ).limit(limit)

        response = await self.db.fetch_all(stmt)

        return [x.tag for x in response]
