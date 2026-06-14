"""Sqlalchemy database."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

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

        self.session_maker = async_sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
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
