"""Search repository."""
import abc

import sqlalchemy as sa
from sqlalchemy.sql import Select

from omoide import const
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
        collections: bool,
    ) -> Select:
        """Add access control and filtering."""
        stmt = stmt.join(
            db_models.ComputedTags,
            db_models.ComputedTags.item_uuid == db_models.Item.uuid,
        )

        stmt = queries.ensure_user_has_permissions(user, stmt)

        if tags_include:
            stmt = stmt.where(
                db_models.ComputedTags.tags.contains(tuple(tags_include)),
            )

        if tags_exclude:
            stmt = stmt.where(
                ~db_models.ComputedTags.tags.overlap(tuple(tags_exclude)),
            )

        if collections:
            stmt = stmt.where(db_models.Item.is_collection == True)  # noqa

        return stmt


class SearchRepository(_SearchRepositoryBase):
    """Repository that performs all search queries."""

    async def count(
        self,
        user: models.User,
        tags_include: set[str],
        tags_exclude: set[str],
        collections: bool,
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
            collections=collections,
        )

        response = await self.db.fetch_one(stmt)

        return int(response['total_items'])

    async def search(
        self,
        user: models.User,
        tags_include: set[str],
        tags_exclude: set[str],
        collections: bool,
        order: const.ORDER_TYPE,
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
            collections=collections,
        )

        stmt = queries.apply_order(
            stmt=stmt,
            order=order,
            last_seen=last_seen,
        )

        stmt = stmt.limit(limit)

        response = await self.db.fetch_all(stmt)

        return [models.Item(**row) for row in response]

    async def get_home_items_for_anon(
        self,
        user: models.User,
        collections: bool,
        nested: bool,
        order: const.ORDER_TYPE,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return home items for anon."""
        stmt = sa.select(
            db_models.Item
        ).where(
            db_models.Item.owner_uuid.in_(  # noqa
                sa.select(db_models.PublicUsers.user_uuid)
            )
        )

        if collections:
            stmt = stmt.where(db_models.Item.is_collection == True)  # noqa

        if nested:
            stmt = stmt.where(db_models.Item.parent_uuid == None)  # noqa

        stmt = queries.apply_order(stmt, order, last_seen)
        stmt = stmt.limit(limit)

        response = await self.db.fetch_all(stmt)
        return [models.Item(**row) for row in response]

    async def get_home_items_for_known(
        self,
        user: models.User,
        collections: bool,
        nested: bool,
        order: const.ORDER_TYPE,
        last_seen: int,
        limit: int,
    ) -> list[models.Item]:
        """Return home items for known user."""
        stmt = sa.select(
            db_models.Item
        ).where(
            sa.or_(
                db_models.Item.owner_uuid == user.uuid,
                db_models.Item.permissions.any(str(user.uuid)),
            )
        )

        if collections:
            stmt = stmt.where(db_models.Item.is_collection == True)  # noqa

        if nested:
            stmt = stmt.where(db_models.Item.parent_uuid == None)  # noqa

        stmt = queries.apply_order(stmt, order, last_seen)
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
