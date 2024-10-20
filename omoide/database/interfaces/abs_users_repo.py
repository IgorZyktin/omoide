"""Repository that perform operations on users."""

import abc
from typing import Collection
from typing import Generic
from typing import TypeVar
from uuid import UUID

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsUsersRepo(Generic[ConnectionT], abc.ABC):
    """Repository that perform operations on users."""

    @abc.abstractmethod
    def get_by_id(self, conn: ConnectionT, user_id: int) -> models.User:
        """Return User with given id."""

    @abc.abstractmethod
    def get_by_uuid(self, conn: ConnectionT, uuid: UUID) -> models.User:
        """Return User with given UUID."""

    @abc.abstractmethod
    def select(
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
