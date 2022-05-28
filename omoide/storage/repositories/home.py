# -*- coding: utf-8 -*-
"""Repository that show items at the home endpoint.
"""
import sqlalchemy
from sqlalchemy import func, desc

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models
from omoide.storage.repositories import base


class HomeRepository(
    base.BaseRepository,
    interfaces.AbsHomeRepository,
):
    """Repository that show items at the home endpoint."""

    async def find_home_items(
            self,
            user: domain.User,
            aim: domain.Aim,
    ) -> list[domain.Item]:
        """Find home items for unauthorised user."""
        if user.is_anon():
            subquery = sqlalchemy.select(models.PublicUsers.user_uuid)
            conditions = [
                models.Item.owner_uuid.in_(subquery)  # noqa
            ]

        else:
            conditions = [
                sqlalchemy.or_(
                    models.Item.owner_uuid == user.uuid,
                    models.ComputedPermissions.permissions.any(user.uuid),
                )
            ]

        if aim.nested:
            conditions.append(models.Item.parent_uuid == None)  # noqa

        if aim.ordered:
            conditions.append(models.Item.number > aim.last_seen)

        stmt = sqlalchemy.select(
            models.Item.uuid,
            models.Item.parent_uuid,
            models.Item.owner_uuid,
            models.Item.number,
            models.Item.name,
            models.Item.is_collection,
            models.Item.content_ext,
            models.Item.preview_ext,
            models.Item.thumbnail_ext,
        )

        if user.is_not_anon():
            stmt = stmt.select_from(
                models.Item.__table__.join(
                    models.ComputedPermissions,
                    models.Item.uuid == models.ComputedPermissions.item_uuid,
                    isouter=True,
                )
            )

        stmt = stmt.where(*conditions)

        if aim.ordered:
            stmt = stmt.order_by(
                desc(models.Item.is_collection),
                models.Item.number,
            )
        else:
            stmt = stmt.order_by(func.random())

        stmt = stmt.limit(aim.items_per_page)

        response = await self.db.fetch_all(stmt)
        # TODO - damn asyncpg tries to bee too smart
        items = [
            domain.Item.from_map(dict(zip(row.keys(), row.values())))
            for row in response
        ]
        return items
