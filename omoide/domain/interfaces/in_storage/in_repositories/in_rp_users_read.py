# -*- coding: utf-8 -*-
"""Repository that performs read operations on users.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_base


class AbsUsersReadRepository(in_rp_base.AbsBaseRepository):
    """Repository that performs read operations on users."""

    @abc.abstractmethod
    async def read_user(
            self,
            uuid: UUID,
    ) -> Optional[domain.User]:
        """Return User or None."""

    @abc.abstractmethod
    async def read_user_by_login(
            self,
            login: str,
    ) -> Optional[domain.User]:
        """Return User or None."""

    @abc.abstractmethod
    async def read_all_users(
            self,
            uuids: list[UUID],
    ) -> list[domain.User]:
        """Return list of users with given uuids."""
