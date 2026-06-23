"""Sqlalchemy database."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Literal
from typing import Self

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

    async def __aenter__(self) -> Self:
        """Start connect to DB."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Disconnect form DB."""
        await self.disconnect()
        return False

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
