"""Repository that performs operations on users."""

from collections.abc import Collection
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Connection

from omoide import exceptions
from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_users_repo import AbsUsersRepo


class UsersRepo(AbsUsersRepo[Connection]):
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
        )

    def get_by_id(
        self,
        conn: Connection,
        user_id: int,
    ) -> models.User:
        """Return User with given id."""
        stmt = sa.select(db_models.User).where(db_models.User.id == user_id)
        response = conn.execute(stmt).first()

        if response is None:
            msg = 'User with ID {user_id} does not exist'
            raise exceptions.DoesNotExistError(msg, user_id=user_id)

        return self._user_from_response(response)

    def get_by_uuid(
        self,
        conn: Connection,
        uuid: UUID,
    ) -> models.User:
        """Return User with given UUID."""
        stmt = sa.select(db_models.User).where(db_models.User.uuid == uuid)
        response = conn.execute(stmt).first()

        if response is None:
            msg = 'User with UUID {user_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, user_uuid=uuid)

        return self._user_from_response(response)

    def select(
        self,
        conn: Connection,
        user_id: int | None = None,
        uuid: UUID | None = None,
        login: str | None = None,
        ids: Collection[int] | None = None,
        uuids: Collection[UUID] | None = None,
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

        stmt = stmt.order_by(db_models.User.id)

        if limit is not None:
            stmt = stmt.limit(limit)

        response = conn.execute(stmt).fetchall()
        return [self._user_from_response(row) for row in response]
