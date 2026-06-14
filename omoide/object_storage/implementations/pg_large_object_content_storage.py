"""Content storage backed by a PostgreSQL large object."""

from collections.abc import AsyncIterable
from typing import Any

from asyncpg_lostream.lostream import PGLargeObject

from omoide.database.implementations.impl_sqlalchemy.database import SqlalchemyDatabase
from omoide.object_storage.interfaces.abs_content_storage import AbsContentStorage


class PgLargeObjectContentStorage(AbsContentStorage):
    """Stream uploads straight into a PostgreSQL large object.

    Opens its own short-lived session so the streaming is independent of
    any business-logic transaction held by the caller. If the upload is
    aborted mid-stream (client disconnect, exception in the use case),
    the session is closed without ``commit()`` and PostgreSQL rolls back
    the ``lo_create`` — no orphan large objects are left behind.
    """

    def __init__(self, database: SqlalchemyDatabase) -> None:
        """Initialize instance."""
        self.database = database

    async def save(self, chunks: AsyncIterable[bytes]) -> dict[str, Any]:
        """Stream ``chunks`` into a new large object and return its OID."""
        async with self.database.session_maker() as session:
            lob_oid = await PGLargeObject.create_large_object(session)
            pgl = PGLargeObject(session, lob_oid, mode='w')
            pgl.writes = 0

            async for chunk in chunks:
                if chunk:
                    await pgl.write(chunk)

            await session.commit()

        return {'oid': int(lob_oid)}
