"""Fixtures shared by parallel worker tests.

These tests run against a real PostgreSQL instance per CLAUDE.md §1. Each
test depends (directly or transitively) on the function-scoped ``engine``
fixture from the parent conftest, which truncates ``command_queue_parallel``
and ``items``/``users`` and unlinks every large object between tests.

The fixtures here:
* ``parallel_db``       — ``ParallelPostgreSQLDatabase`` wired to the test DB.
* ``lock_provider``     — connected ``PGAdvisoryLock`` against the test DB.
* ``object_storage``    — ``PgLargeObjectStorage`` sharing parallel_db's engine.
* ``stub_config``       — minimal config object exposing the fields the
                          worker loop reads.
* ``make_parallel_command`` — factory that inserts a ``command_queue_parallel``
                              row and returns the domain ``ParallelCommand``.
* ``_read_status`` / ``_large_object_exists`` — small read-back helpers.

The bulk of the worker-loop tests use ``DummyCommand``: it has no required
resources, no side effects, and a trivial ``execute()``. That isolates the
loop/lock/cleanup contract from any specific command's business logic, which
is exactly what we want to verify here.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Engine

from omoide import models
from omoide.database import db_models
from omoide.infra.implementations.pg_advisory_lock import PGAdvisoryLock
from omoide.infra.locators import FilesystemLocator
from omoide.object_storage.implementations.pgl_object_storage import (
    PgLargeObjectStorage,
)
from omoide.workers.parallel.database import ParallelPostgreSQLDatabase


@dataclass
class StubConfig:
    """Minimal config exposing fields the worker loop reads."""

    input_batch: int = 10
    supported_operations: frozenset[str] = field(default_factory=lambda: frozenset(['dummy']))
    data_folder: Path = field(default_factory=Path)
    prefix_size: int = 2
    name: str = 'parallel-test'
    delay: float = 0.0
    workers: int = 0
    max_workers: int = 1


@pytest.fixture
def stub_config(tmp_path: Path) -> StubConfig:
    """Return a config object pointing at a per-test tmp scratch folder."""
    return StubConfig(data_folder=tmp_path)


@pytest.fixture
def make_parallel_command(engine: Engine, make_user):
    """Insert a ``command_queue_parallel`` row; return the domain model.

    Defaults yield a ``dummy``-name command in ``created`` state with no
    ``extras`` — perfect for the loop tests below. Callers override to
    test specific paths.
    """

    def _factory(
        *,
        name: str = 'dummy',
        extras: dict[str, Any] | None = None,
        status: str = models.CommandStatus.CREATED.value,
        requested_by: int | None = None,
    ) -> models.ParallelCommand:
        now = datetime.now(UTC)
        if requested_by is None:
            requested_by, _ = make_user()

        with engine.begin() as conn:
            result = conn.execute(
                sa.insert(db_models.ParallelCommand)
                .values(
                    requested_by=requested_by,
                    name=name,
                    status=status,
                    extras=extras or {},
                    log='',
                    created_at=now,
                    updated_at=now,
                    started_at=None,
                    ended_at=None,
                )
                .returning(db_models.ParallelCommand)
            )
            row = result.one()

        return models.ParallelCommand(
            id=row.id,
            requested_by=row.requested_by,
            name=row.name,
            status=models.CommandStatus(row.status),
            extras=row.extras,
            log=row.log,
            created_at=row.created_at,
            updated_at=row.updated_at,
            started_at=row.started_at,
            ended_at=row.ended_at,
        )

    return _factory


@pytest.fixture
async def parallel_db(
    async_db_url: str,
    _schema_engine: Engine,
    engine: Engine,
) -> AsyncIterator[ParallelPostgreSQLDatabase]:
    """``ParallelPostgreSQLDatabase`` connected to the test DB.

    Depends on ``_schema_engine`` so the schema is bootstrapped, and on
    ``engine`` so the per-test truncate cycle applies before any async
    work runs.
    """
    _ = _schema_engine
    _ = engine
    db = ParallelPostgreSQLDatabase(async_db_url)
    await db.connect()
    try:
        yield db
    finally:
        await db.disconnect()


@pytest.fixture
async def lock_provider(
    async_db_url: str,
    _schema_engine: Engine,
    engine: Engine,
) -> AsyncIterator[PGAdvisoryLock]:
    """Return connected ``PGAdvisoryLock`` against the test DB."""
    _ = _schema_engine
    _ = engine
    provider = PGAdvisoryLock(async_db_url)
    await provider.connect()
    try:
        yield provider
    finally:
        await provider.disconnect()


@pytest.fixture
def object_storage(
    parallel_db: ParallelPostgreSQLDatabase,
) -> PgLargeObjectStorage:
    """``PgLargeObjectStorage`` reusing parallel_db's engine."""
    return PgLargeObjectStorage(parallel_db)


@pytest.fixture
def fs_locator(tmp_path: Path) -> FilesystemLocator:
    """File locator rooted at the per-test tmp directory."""
    return FilesystemLocator(root=tmp_path, prefix_size=2)


def _read_status(engine: Engine, command_id: int) -> str:
    """Return the current status of a command row, or '' if missing."""
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(db_models.ParallelCommand.status).where(
                db_models.ParallelCommand.id == command_id
            )
        ).fetchone()
    return '' if row is None else str(row.status)


def _read_log(engine: Engine, command_id: int) -> str:
    """Return the current log column of a command row."""
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(db_models.ParallelCommand.log).where(
                db_models.ParallelCommand.id == command_id
            )
        ).fetchone()
    assert row is not None
    return str(row.log)


def _large_object_exists(engine: Engine, oid: int) -> bool:
    """Return True iff a large object with this OID exists in PG."""
    with engine.connect() as conn:
        row = conn.execute(
            sa.text('SELECT 1 FROM pg_largeobject_metadata WHERE oid = :oid'),
            {'oid': oid},
        ).scalar()
    return row is not None


async def _save_small_large_object(storage: PgLargeObjectStorage, payload: bytes = b'x') -> int:
    """Stream a payload into a new LOB; return its OID."""

    async def _chunks():
        yield payload

    result = await storage.write(_chunks())
    return int(result['oid'])
