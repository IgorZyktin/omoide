# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on users and their data.
"""
import abc
from typing import Optional, Any
from uuid import UUID

from omoide import domain
from omoide.presentation import api_models


class AbsUsersRepository(abc.ABC):
    """Repository that perform CRUD operations on users and their data."""

    def __init__(self, db) -> None:  # TODO - move to base class
        """Initialize instance."""
        self.db = db

    def transaction(self) -> Any:  # TODO - move to base class
        """Start transaction."""
        return self.db.transaction()

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
