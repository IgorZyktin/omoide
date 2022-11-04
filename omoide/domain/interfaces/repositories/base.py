# -*- coding: utf-8 -*-
"""Base repository class.
"""
import abc
from typing import Any
from typing import Optional
from uuid import UUID

from omoide.domain import auth
from omoide.domain import common


# TODO: remove this class
class AbsRepository(abc.ABC):
    """Base repository class."""

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    def transaction(self) -> Any:
        """Start transaction."""
        return self.db.transaction()

    @abc.abstractmethod
    async def user_is_public(
            self,
            owner_uuid: str,
    ) -> bool:
        """Return True if owner is a public user."""

    @abc.abstractmethod
    async def get_user(
            self,
            user_uuid: UUID,
    ) -> Optional[auth.User]:
        """Return user or None."""


class AbsBaseRepository(abc.ABC):
    """Base repository class."""

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    def transaction(self) -> Any:
        """Start transaction."""
        return self.db.transaction()
