"""Repository that performs operations on users."""

from collections.abc import Collection
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.storage import interfaces
from omoide.database import db_models


class UsersRepo(interfaces.AbsUsersRepo):
    """Repository that performs operations on users."""

    @staticmethod
    def _user_from_response(response: Any) -> models.User:
        """Convert DB response to user model."""
        return models.User(
            id=response.id,
            uuid=response.uuid,
            name=response.name,
            login=response.login,
            role=response.role,
            is_public=response.is_public,
            registered_at=response.registered_at,
            last_login=response.last_login,
        )

    async def create_user(
        self,
        user: models.User,
        encoded_password: str,
        auth_complexity: int,
    ) -> None:
        """Create new user."""
        stmt = sa.insert(db_models.User).values(
            uuid=user.uuid,
            login=user.login,
            password=encoded_password,
            auth_complexity=auth_complexity,
            role_id=user.role,
            is_public=user.is_public,
            registered_at=utils.now(),
            last_login=None,
        )

        await self.db.execute(stmt)

    async def get_user_by_id(self, user_id: int) -> models.User:
        """Return User."""
        stmt = sa.select(db_models.User).where(db_models.User.id == user_id)
        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'User with ID {user_id} does not exist'
            raise exceptions.DoesNotExistError(msg, user_id=user_id)

        return self._user_from_response(response)

    async def get_user_by_uuid(self, uuid: UUID) -> models.User:
        """Return User."""
        stmt = sa.select(db_models.User).where(db_models.User.uuid == uuid)
        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'User with UUID {user_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, user_uuid=uuid)

        return self._user_from_response(response)

    async def get_user_by_login(
        self,
        login: str,
    ) -> tuple[models.User, str, int] | None:
        """Return user+password for given login."""
        stmt = sa.select(db_models.User).where(db_models.User.login == login)
        response = await self.db.fetch_one(stmt)

        if response is None:
            return None

        user = self._user_from_response(response)
        return user, response.password, response.auth_complexity

    async def get_users(
        self,
        user_id: int | None = None,
        uuid: UUID | None = None,
        login: str | None = None,
        ids: Collection[int] | None = None,
        uuids: Collection[UUID] | None = None,
        logins: Collection[str] | None = None,
        limit: int | None = None,
    ) -> list[models.User]:
        """Return filtered list of users."""
        stmt = sa.select(db_models.User)

        if user_id is not None:
            stmt = stmt.where(db_models.User.id == user_id)

        if uuid is not None:
            stmt = stmt.where(db_models.User.uuid == uuid)

        if login is not None:
            stmt = stmt.where(db_models.User.login == login)

        if ids is not None:
            stmt = stmt.where(db_models.User.id.in_(tuple(ids)))

        if uuids is not None:
            stmt = stmt.where(db_models.User.uuid.in_(tuple(uuids)))

        if logins is not None:
            stmt = stmt.where(db_models.User.login.in_(tuple(logins)))

        if limit is not None:
            stmt = stmt.limit(limit)

        response = await self.db.fetch_all(stmt)

        return [self._user_from_response(row) for row in response]

    async def update_user(self, uuid: UUID, **kwargs: Any) -> None:
        """Update User."""
        stmt = (
            sa.update(db_models.User)
            .where(db_models.User.uuid == uuid)
            .values(**kwargs)
        )
        await self.db.execute(stmt)

    async def calc_total_space_used_by(
        self,
        user: models.User,
    ) -> models.SpaceUsage:
        """Return total amount of used space for user."""
        stmt = (
            sa.select(
                sa.func.sum(db_models.Metainfo.content_size).label(
                    'content_size'
                ),
                sa.func.sum(db_models.Metainfo.preview_size).label(
                    'preview_size'
                ),
                sa.func.sum(db_models.Metainfo.thumbnail_size).label(
                    'thumbnail_size'
                ),
            )
            .join(
                db_models.Item,
                db_models.Item.uuid == db_models.Metainfo.item_uuid,
            )
            .where(db_models.Item.owner_uuid == str(user.uuid))
        )

        response = await self.db.fetch_one(stmt)

        return models.SpaceUsage(
            uuid=user.uuid,
            content_size=response['content_size'] or 0,
            preview_size=response['preview_size'] or 0,
            thumbnail_size=response['thumbnail_size'] or 0,
        )

    async def get_public_user_uuids(self) -> set[UUID]:
        """Return set of UUIDs of public users."""
        stmt = sa.select(db_models.PublicUsers.user_uuid)

        response = await self.db.fetch_all(stmt)

        if response is None:
            return set()

        return {x['user_uuid'] for x in response}
