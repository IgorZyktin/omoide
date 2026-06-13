"""Abstract database."""

import abc
from collections.abc import AsyncIterable
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Generic
from typing import TypeVar

ConnectionT = TypeVar('ConnectionT')


class AbsDatabase(abc.ABC, Generic[ConnectionT]):
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

    @abc.abstractmethod
    async def save_large_object(self, chunks: AsyncIterable[bytes]) -> int:
        """Stream ``chunks`` into a large object and return its OID."""
