"""Repository that performs operations on users."""

import abc
from collections.abc import Collection
from uuid import UUID

from omoide import models


class AbsUsersRepo(abc.ABC):
    """Repository that performs read operations on users."""

    @abc.abstractmethod
    async def create_user(
        self,
        user: models.User,
        encoded_password: str,
        auth_complexity: int,
    ) -> None:
        """Create new user."""

    @abc.abstractmethod
    async def get_user_by_id(self, user_id: int) -> models.User:
        """Return User."""

    @abc.abstractmethod
    async def get_user_by_uuid(self, uuid: UUID) -> models.User:
        """Return User."""

    @abc.abstractmethod
    async def get_user_by_login(
        self,
        login: str,
    ) -> tuple[models.User, str, int] | None:
        """Return user+password for given login."""

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
    async def update_user(self, uuid: UUID, **kwargs: str) -> None:
        """Update User."""

    @abc.abstractmethod
    async def calc_total_space_used_by(
        self,
        user: models.User,
    ) -> models.SpaceUsage:
        """Return total amount of used space for user."""

    @abc.abstractmethod
    async def get_public_user_uuids(self) -> set[UUID]:
        """Return set of UUIDs for public users."""
