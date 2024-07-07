"""Repository that performs read operations on users."""
from uuid import UUID

import sqlalchemy as sa

from omoide import domain
from omoide import models
from omoide.domain import interfaces
from omoide.storage.database import models as db_models


class UsersRepo(interfaces.AbsUsersRepo):
    """Repository that performs read operations on users."""

    async def read_user(self, uuid: UUID) -> models.User | None:
        """Return User or None."""
        stmt = sa.select(db_models.User).where(db_models.User.uuid == uuid)

        response = await self.db.fetch_one(stmt)

        if response:
            user = models.User(**response, role=models.Role.user)
            return user

        return None

    async def read_filtered_users(
        self,
        *uuids: UUID,
        login: str | None = None,
    ) -> list[models.User]:
        """Return list of users with given uuids or filters."""
        if not any((bool(uuids), bool(login))):
            return []

        stmt = sa.select(db_models.User)

        if login:
            stmt = stmt.where(db_models.User.login == login)

        if uuids:
            stmt = stmt.where(
                db_models.User.uuid.in_(tuple(str(x) for x in uuids))  # noqa
            )

        stmt = stmt.order_by(db_models.User.name)

        response = await self.db.fetch_all(stmt)
        return [
            models.User(**record, role=models.Role.user)
            for record in response
        ]

    async def read_all_users(self) -> list[models.User]:
        """Return list of users with given uuids (or all users)."""
        stmt = sa.select(db_models.User).order_by(db_models.User.name)
        response = await self.db.fetch_all(stmt)
        return [
            models.User(**record, role=models.Role.user)
            for record in response
        ]

    async def calc_total_space_used_by(
        self,
        user: models.User,
    ) -> domain.SpaceUsage:
        """Return total amount of used space for user."""
        stmt = sa.select(
            sa.func.sum(db_models.Metainfo.content_size).label(
                'content_size'
            ),
            sa.func.sum(db_models.Metainfo.preview_size).label(
                'preview_size'
            ),
            sa.func.sum(db_models.Metainfo.thumbnail_size).label(
                'thumbnail_size'
            )
        ).join(
            db_models.Item,
            db_models.Item.uuid == db_models.Metainfo.item_uuid,
        ).where(
            db_models.Item.owner_uuid == str(user.uuid)
        )
        response = await self.db.fetch_one(stmt)
        return domain.SpaceUsage(
            uuid=user.uuid,
            content_size=response['content_size'] or 0,
            preview_size=response['preview_size'] or 0,
            thumbnail_size=response['thumbnail_size'] or 0,
        )

    async def user_is_public(self, uuid: UUID) -> bool:
        """Return True if given user is public."""
        stmt = sa.select(
            db_models.PublicUsers.user_uuid
        ).where(
            db_models.PublicUsers.user_uuid == uuid
        )
        response = await self.db.fetch_one(stmt)
        return response is not None

    async def get_public_users_uuids(self) -> set[UUID]:
        """Return set of UUIDs of public users."""
        stmt = sa.select(db_models.PublicUsers.user_uuid)

        response = await self.db.fetch_all(stmt)

        if response is None:
            return set()

        return set(x['user_uuid'] for x in response)
