# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on users and their data.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.repositories import base
from omoide.presentation import api_models


class AbsUsersRepository(base.AbsBaseRepository):
    """Repository that perform CRUD operations on users and their data."""

    @abc.abstractmethod
    async def generate_user_uuid(self) -> UUID:
        """Generate new UUID4 for user."""

    @abc.abstractmethod
    async def create_user(
            self,
            payload: api_models.CreateUserIn,
            password: bytes,
    ) -> UUID:
        """Return UUID for created user."""

    @abc.abstractmethod
    async def read_user(
            self,
            uuid: UUID,
    ) -> Optional[domain.User]:
        """Return user or None."""

    @abc.abstractmethod
    async def read_all_users(
            self,
            uuids: list[UUID | str],
    ) -> list[domain.User]:
        """Return list of users with given uuids."""

    @abc.abstractmethod
    async def update_user(
            self,
            user: domain.User,
    ) -> UUID:
        """Update existing user."""
