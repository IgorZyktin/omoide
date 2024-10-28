"""Repository that perform operations on users."""

import abc
from collections.abc import Collection
from typing import Generic
from typing import TypeVar
from uuid import UUID

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsUsersRepo(Generic[ConnectionT], abc.ABC):
    """Repository that perform operations on users."""

    @abc.abstractmethod
    async def create(
        self,
        conn: ConnectionT,
        user: models.User,
        encoded_password: str,
        auth_complexity: int,
    ) -> int:
        """Create new user."""

    @abc.abstractmethod
    async def get_by_id(self, conn: ConnectionT, user_id: int) -> models.User:
        """Return User with given id."""

    @abc.abstractmethod
    async def get_by_uuid(self, conn: ConnectionT, uuid: UUID) -> models.User:
        """Return User with given UUID."""

    @abc.abstractmethod
    async def select(
        self,
        conn: ConnectionT,
        user_id: int | None = None,
        uuid: UUID | None = None,
        login: str | None = None,
        ids: Collection[int] | None = None,
        uuids: Collection[UUID] | None = None,
        limit: int | None = None,
    ) -> list[models.User]:
        """Return filtered list of users."""

    @abc.abstractmethod
    async def delete(self, conn: ConnectionT, user: models.User) -> bool:
        """Delete given user."""

    @abc.abstractmethod
    async def get_public_user_uuids(self, conn: ConnectionT) -> set[UUID]:
        """Return UUIDs of public users."""

    @abc.abstractmethod
    async def get_root_item(self, conn: ConnectionT, user: models.User) -> models.Item:
        """Return root item for given user."""
