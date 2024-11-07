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
    async def get_by_login(
        self,
        conn: ConnectionT,
        login: str,
    ) -> tuple[models.User, str, int] | None:
        """Return user+password for given login."""

    @abc.abstractmethod
    async def get_map(
        self,
        conn: ConnectionT,
        items: Collection[models.Item],
        permissions: bool = True,
        owners: bool = False,
    ) -> dict[int, models.User | None]:
        """Get map of users for given items."""

    @abc.abstractmethod
    async def select(  # noqa: PLR0913 Too many arguments in function definition
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
    async def save(self, conn: ConnectionT, user: models.User) -> bool:
        """Save given user."""

    @abc.abstractmethod
    async def delete(self, conn: ConnectionT, user: models.User) -> bool:
        """Delete given user."""

    @abc.abstractmethod
    async def get_public_user_ids(self, conn: ConnectionT) -> set[int]:
        """Return ids of public users."""

    @abc.abstractmethod
    async def get_root_item(self, conn: ConnectionT, user: models.User) -> models.Item:
        """Return root item for given user."""

    @abc.abstractmethod
    async def get_root_items_map(
        self,
        conn: ConnectionT,
        *users: models.User,
    ) -> dict[int, models.Item | None]:
        """Return map of root items."""

    @abc.abstractmethod
    async def calc_total_space_used_by(
        self,
        conn: ConnectionT,
        user: models.User,
    ) -> models.SpaceUsage:
        """Return total amount of used space for user."""

    @abc.abstractmethod
    async def count_items_by_owner(
        self,
        conn: ConnectionT,
        user: models.User,
        collections: bool = False,
    ) -> int:
        """Return total amount of items for given user uuid."""

    @abc.abstractmethod
    async def update_user_password(
        self,
        conn: ConnectionT,
        user: models.User,
        new_password: str,
    ) -> None:
        """Save new user password (this field is not a part of the user model)."""

    @abc.abstractmethod
    async def cast_uuids(self, conn: ConnectionT, uuids: Collection[UUID]) -> set[int]:
        """Convert collection of `user_uuid` into set of `user_id`."""
