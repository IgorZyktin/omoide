"""PostgreSQL advisory lock implementation."""

from collections.abc import Sequence
from types import TracebackType
from typing import Literal
from typing import Self

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from omoide import custom_logging
from omoide.infra.interfaces.abs_lock import AbsLockingProvider
from omoide.infra.interfaces.abs_lock import LockableResource

LOG = custom_logging.get_logger(__name__)

_TRY_LOCK = sa.text('SELECT pg_try_advisory_lock(:ns, :id)')
_UNLOCK = sa.text('SELECT pg_advisory_unlock(:ns, :id)')
_UNLOCK_ALL = sa.text('SELECT pg_advisory_unlock_all()')


class PGAdvisoryLock(AbsLockingProvider):
    """Advisory-lock provider backed by a dedicated AUTOCOMMIT connection.

    The connection is checked out of the pool on connect() and held for
    the lifetime of the provider — advisory locks are session-scoped, so
    returning the connection to the pool would leak them to the next
    user. AUTOCOMMIT prevents the first execute() from opening an
    implicit transaction that never closes — that would block VACUUM and
    bloat WAL for as long as the worker runs.
    """

    def __init__(self, db_url: str) -> None:
        """Initialize instance."""
        self._engine = create_async_engine(db_url, poolclass=NullPool)
        self._conn: AsyncConnection | None = None

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

    @property
    def _connection(self) -> AsyncConnection:
        """Return the dedicated lock connection."""
        if self._conn is None:
            msg = 'Lock connection was not established; call connect() first'
            raise RuntimeError(msg)
        return self._conn

    async def connect(self) -> None:
        """Open the dedicated AUTOCOMMIT lock connection."""
        if self._conn is not None:
            return

        conn = await self._engine.connect()
        self._conn = await conn.execution_options(isolation_level='AUTOCOMMIT')

    async def disconnect(self) -> None:
        """Close the dedicated connection; releases every held lock."""
        if self._conn is None:
            return

        try:
            await self.release_all()
            await self._conn.close()
        finally:
            self._conn = None
            await self._engine.dispose()

    async def acquire(
        self,
        resources: Sequence[LockableResource],
    ) -> list[LockableResource] | None:
        """Lock all resources or none.

        Sorted order is mandatory: two callers locking the same set in
        different orders would deadlock — Postgres detects it but logs
        noise and kills one of them.
        """
        taken: list[LockableResource] = []
        for resource in sorted(resources):
            result = await self._connection.execute(
                _TRY_LOCK,
                {'ns': resource.namespace, 'id': resource.affected_id},
            )
            (ok,) = result.fetchone() or (False,)
            if not ok:
                await self.release_held(taken)
                return None
            taken.append(resource)
        return taken

    async def release_held(
        self,
        resources: Sequence[LockableResource],
    ) -> None:
        """Best-effort release; never raises.

        A False return from pg_advisory_unlock signals that this session
        never held the lock — that is a desync worth logging but not
        worth propagating, otherwise we'd leave callers in a half-released
        state.
        """
        for resource in reversed(resources):
            try:
                result = await self._connection.execute(
                    _UNLOCK,
                    {'ns': resource.namespace, 'id': resource.affected_id},
                )
                (released,) = result.fetchone() or (False,)
                if not released:
                    LOG.warning(
                        'pg_advisory_unlock({}, {}) returned false — '
                        'lock was not held by this session',
                        resource.namespace,
                        resource.affected_id,
                    )
            except Exception:
                LOG.exception(
                    'Failed to release advisory lock ({}, {})',
                    resource.namespace,
                    resource.affected_id,
                )

    async def release_all(self) -> None:
        """Release all resources."""
        try:
            await self._connection.execute(_UNLOCK_ALL)
        except Exception:
            msg = 'Failed to release advisory locks'
            LOG.exception(msg)
