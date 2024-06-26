"""Repository that performs read operations on users.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide.domain import interfaces
from omoide.storage.database import models


class UsersRepository(interfaces.AbsUsersRepository):
    """Repository that performs read operations on users."""

    async def read_user(
            self,
            uuid: UUID,
    ) -> Optional[domain.User]:
        """Return User or None."""
        stmt = sa.select(
            models.User
        ).where(
            models.User.uuid == uuid
        )
        response = await self.db.fetch_one(stmt)
        return domain.User(**response) if response else None

    async def read_user_by_login(
            self,
            login: str,
    ) -> Optional[domain.User]:
        """Return User or None."""
        stmt = sa.select(
            models.User
        ).where(
            models.User.login == login
        )
        response = await self.db.fetch_one(stmt)
        return domain.User(**response) if response else None

    async def read_all_users(
            self,
            *uuids: UUID,
    ) -> list[domain.User]:
        """Return list of users with given uuids."""
        stmt = sa.select(
            models.User
        ).where(
            models.User.uuid.in_(tuple(str(x) for x in uuids))  # noqa
        )

        response = await self.db.fetch_all(stmt)
        return [domain.User(**record) for record in response]

    async def calc_total_space_used_by(
            self,
            user: domain.User,
    ) -> domain.SpaceUsage:
        """Return total amount of used space for user."""
        stmt = sa.select(
            sa.func.sum(models.Metainfo.content_size).label('content_size'),
            sa.func.sum(models.Metainfo.preview_size).label('preview_size'),
            sa.func.sum(models.Metainfo.thumbnail_size).label('thumbnail_size')
        ).join(
            models.Item,
            models.Item.uuid == models.Metainfo.item_uuid,
        ).where(
            models.Item.owner_uuid == str(user.uuid)
        )
        response = await self.db.fetch_one(stmt)
        return domain.SpaceUsage(
            uuid=user.uuid,
            content_size=response['content_size'] or 0,
            preview_size=response['preview_size'] or 0,
            thumbnail_size=response['thumbnail_size'] or 0,
        )

    async def user_is_public(
            self,
            uuid: UUID,
    ) -> bool:
        """Return True if given user is public."""
        stmt = sa.select(
            models.PublicUsers.user_uuid
        ).where(
            models.PublicUsers.user_uuid == uuid
        )
        response = await self.db.fetch_one(stmt)
        return response is not None

    async def get_public_users_uuids(
            self,
    ) -> set[UUID]:
        """Return set of UUIDs of public users."""
        stmt = sa.select(
            models.PublicUsers.user_uuid
        )

        response = await self.db.fetch_all(stmt)
        if response is None:
            return set()
        return set(x['user_uuid'] for x in response)
