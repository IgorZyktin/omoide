"""Base class for all databases."""

import abc
from contextlib import asynccontextmanager
from typing import AsyncIterator
from typing import Generic
from typing import TypeVar

ConnectionT = TypeVar('ConnectionT')


class AbsDatabase(Generic[ConnectionT], abc.ABC):
    """Base class for all databases."""

    @abc.abstractmethod
    async def connect(self) -> None:
        """Connect to the database."""

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the database."""

    @asynccontextmanager
    @abc.abstractmethod
    def transaction(self) -> AsyncIterator[ConnectionT]:
        """Start transaction."""
