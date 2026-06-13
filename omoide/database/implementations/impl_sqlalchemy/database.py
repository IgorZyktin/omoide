"""Sqlalchemy database."""

from collections.abc import AsyncIterable
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from asyncpg_lostream.lostream import PGLargeObject
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

        self._session_maker = async_sessionmaker(
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

    async def save_large_object(self, chunks: AsyncIterable[bytes]) -> int:
        """Stream ``chunks`` into a large object and return its OID."""
        async with self._session_maker() as session:
            lob_oid = await PGLargeObject.create_large_object(session)
            pgl = PGLargeObject(session, lob_oid, mode='w')
            pgl.writes = 0

            async for chunk in chunks:
                if chunk:
                    await pgl.write(chunk)

            await session.commit()

        return int(lob_oid)
