# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on users and their data.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.presentation import api_models


class AbsUsersRepository(abc.ABC):
    """Repository that perform CRUD operations on users and their data."""

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    @abc.abstractmethod
    def transaction(self):
        """Start transaction."""
        # FIXME: parent repository should have this method

    @abc.abstractmethod
    async def generate_uuid(self) -> UUID:
        """Generate new UUID4 for an item."""

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
    async def update_user(
            self,
            user: domain.User,
    ) -> UUID:
        """Update existing user."""
