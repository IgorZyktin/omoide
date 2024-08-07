"""Repository that performs read operations on users."""
from uuid import UUID
from uuid import uuid4

import sqlalchemy as sa

from omoide import exceptions
from omoide import models
from omoide.storage import interfaces
from omoide.storage.implementations.asyncpg.asyncpg_storage import (
    AsyncpgStorage
)
from omoide.storage.database import db_models


class UsersRepo(interfaces.AbsUsersRepo, AsyncpgStorage):
    """Repository that performs read operations on users."""

    async def get_free_uuid(self) -> UUID:
        """Generate new unused UUID4."""
        while True:
            uuid = uuid4()

            stmt = sa.select(
                db_models.User.uuid
            ).where(
                db_models.User.uuid == uuid
            ).exists()

            exists = await self.db.fetch_one(stmt, {'uuid': uuid})

            if not exists:
                return uuid

    async def create_user(
        self,
        user: models.User,
        auth_complexity: int,
    ) -> None:
        """Create new user."""
        stmt = sa.insert(
            db_models.User
        ).values(
            uuid=user.uuid,
            login=user.login,
            password=user.password,
            auth_complexity=auth_complexity,
        )

        await self.db.execute(stmt)

    async def read_user(self, uuid: UUID) -> models.User | None:
        """Return User or None."""
        stmt = sa.select(db_models.User).where(db_models.User.uuid == uuid)

        response = await self.db.fetch_one(stmt)

        if response:
            user = models.User(**response, role=models.Role.user)
            return user

        return None

    async def get_user(self, uuid: UUID) -> models.User:
        """Return User."""
        stmt = sa.select(db_models.User).where(db_models.User.uuid == uuid)
        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'User with UUID {user_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, user_uuid=uuid)

        return models.User(**response, role=models.Role.user)

    async def get_user_by_login(
        self,
        login: str,
        allow_absence: bool = False,
    ) -> models.User | None:
        """Return User or None."""
        stmt = sa.select(db_models.User).where(db_models.User.login == login)
        response = await self.db.fetch_one(stmt)

        if response is None:
            if allow_absence:
                return None

            msg = 'User with given login does not exist'
            raise exceptions.DoesNotExistError(msg)

        return models.User(**response, role=models.Role.user)

    async def update_user(self, uuid: UUID, **kwargs: str) -> None:
        """Update User."""
        stmt = sa.update(
            db_models.User
        ).where(
            db_models.User.uuid == uuid
        ).values(
            **kwargs
        )
        await self.db.execute(stmt)

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
    ) -> models.SpaceUsage:
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

        return models.SpaceUsage(
            uuid=user.uuid,
            content_size=response['content_size'] or 0,
            preview_size=response['preview_size'] or 0,
            thumbnail_size=response['thumbnail_size'] or 0,
        )

    async def get_public_users_uuids(self) -> set[UUID]:
        """Return set of UUIDs of public users."""
        stmt = sa.select(db_models.PublicUsers.user_uuid)

        response = await self.db.fetch_all(stmt)

        if response is None:
            return set()

        return set(x['user_uuid'] for x in response)
