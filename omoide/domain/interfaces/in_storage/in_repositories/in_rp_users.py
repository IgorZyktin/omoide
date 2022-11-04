# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on users and their data.
"""
import abc
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.in_storage \
    .in_repositories import in_rp_users_read
from omoide.presentation import api_models


class AbsUsersRepository(in_rp_users_read.AbsUsersReadRepository):
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
        """Create user and return UUID."""

    @abc.abstractmethod
    async def update_user(
            self,
            user: domain.User,
    ) -> UUID:
        """Update existing user."""
