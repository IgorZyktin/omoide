"""Repository that performs operations on users."""
import abc
from typing import Collection
from uuid import UUID

from omoide import models


class AbsUsersRepo(abc.ABC):
    """Repository that performs read operations on users."""

    @abc.abstractmethod
    async def get_free_uuid(self) -> UUID:
        """Generate new unused UUID."""

    @abc.abstractmethod
    async def create_user(
        self,
        user: models.User,
        auth_complexity: int,
    ) -> None:
        """Create new user."""

    # TODO - remove this method
    @abc.abstractmethod
    async def read_user(self, uuid: UUID) -> models.User | None:
        """Return User or None."""

    @abc.abstractmethod
    async def get_user(self, uuid: UUID) -> models.User:
        """Return User."""

    @abc.abstractmethod
    async def get_users(
        self,
        uuid: UUID | None = None,
        login: str | None = None,
        uuids: Collection[UUID] | None = None,
        logins: Collection[str] | None = None,
        limit: int | None = None,
    ) -> list[models.User]:
        """Return filtered list of users."""

    @abc.abstractmethod
    async def get_user_by_login(
        self,
        login: str,
        allow_absence: bool = False,
    ) -> models.User | None:
        """Return User or None."""

    @abc.abstractmethod
    async def update_user(self, uuid: UUID, **kwargs: str) -> None:
        """Update User."""

    @abc.abstractmethod
    async def read_filtered_users(
        self,
        *uuids: UUID,
        login: str | None = None,
    ) -> list[models.User]:
        """Return list of users with given uuids or filters."""

    @abc.abstractmethod
    async def read_all_users(self) -> list[models.User]:
        """Return all users."""

    @abc.abstractmethod
    async def calc_total_space_used_by(
        self,
        user: models.User,
    ) -> models.SpaceUsage:
        """Return total amount of used space for user."""

    @abc.abstractmethod
    async def get_public_users_uuids(self) -> set[UUID]:
        """Return set of UUIDs for public users."""
