"""Sqlalchemy database."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection

from omoide.database.interfaces.abs_database import AbsDatabase


class SqlalchemyDatabase(AbsDatabase[AsyncConnection]):
    """Base class for all databases."""

    def __init__(self, db_url: str, echo: bool = False) -> None:
        """Initialize instance."""
        self._engine = create_async_engine(
            db_url,
            echo=echo,
            pool_pre_ping=True,
        )

    async def connect(self) -> None:
        """Connect to the database."""

    async def disconnect(self) -> None:
        """Disconnect from the database."""
        await self._engine.dispose()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncConnection]:
        """Start transaction."""
        async with self._engine.begin() as connection:
            yield connection
