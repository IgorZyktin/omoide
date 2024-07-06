"""Repository that performs operations on users.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide import models
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_base


class AbsUsersRepo(in_rp_base.AbsBaseRepository):
    """Repository that performs read operations on users."""

    @abc.abstractmethod
    async def read_user(
            self,
            uuid: UUID,
    ) -> Optional[models.User]:
        """Return User or None."""

    @abc.abstractmethod
    async def read_all_users(
            self,
            *uuids: UUID,
            login: str | None = None,
    ) -> list[models.User]:
        """Return list of users with given uuids."""

    @abc.abstractmethod
    async def calc_total_space_used_by(
            self,
            user: models.User,
    ) -> domain.SpaceUsage:
        """Return total amount of used space for user."""

    @abc.abstractmethod
    async def user_is_public(
            self,
            uuid: UUID,
    ) -> bool:
        """Return True if given user is public."""

    @abc.abstractmethod
    async def get_public_users_uuids(
            self,
    ) -> set[UUID]:
        """Return set of UUIDs of public users."""
