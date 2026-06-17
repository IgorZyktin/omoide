"""Integration tests for ``WorkersRepo``.

Per CLAUDE.md §1 these MUST run against a real PostgreSQL instance and
MUST NOT mock the database. Each test depends on the function-scoped
``engine`` fixture, which truncates ``serial_lock`` and
``serial_operations`` between tests.
"""

from datetime import UTC
from datetime import datetime

import pytest
import sqlalchemy as sa

from omoide import operations
from omoide.database import db_models
from omoide.database.implementations import impl_sqlalchemy


@pytest.fixture
def workers_repo() -> impl_sqlalchemy.WorkersRepo:
    """Provide a ``WorkersRepo`` instance."""
    return impl_sqlalchemy.WorkersRepo()


@pytest.fixture
def seed_serial_lock(engine):
    """Insert the single empty SerialLock row.

    The migration creates the table empty; ops insert one row by hand in
    production. The truncate fixture wipes it between tests, so each test
    that exercises the lock must re-seed.
    """
    with engine.begin() as conn:
        conn.execute(
            sa.insert(db_models.SerialLock).values(
                worker_name=None,
                last_update=datetime.now(UTC),
            )
        )


@pytest.fixture
def make_serial_operation(engine):
    """Insert a serial_operations row; return its id."""

    def _factory(
        *,
        name: str = 'test_op',
        status: str = operations.OperationStatus.CREATED.value,
    ) -> int:
        now = datetime.now(UTC)
        with engine.begin() as conn:
            result = conn.execute(
                sa.insert(db_models.SerialOperation)
                .values(
                    name=name,
                    status=status,
                    extras={},
                    created_at=now,
                    updated_at=now,
                    started_at=None,
                    ended_at=None,
                    log=None,
                    payload=b'',
                    processed_by=[],
                )
                .returning(db_models.SerialOperation.id)
            )
            return int(result.scalar_one())

    return _factory


def _read_serial_lock_worker(engine) -> str | None:
    with engine.connect() as conn:
        row = conn.execute(sa.select(db_models.SerialLock.worker_name)).fetchone()
    assert row is not None
    return row.worker_name


class TestTakeSerialLock:
    """Verify ``take_serial_lock`` only claims an empty slot."""

    async def test_takes_empty_slot(
        self,
        async_database,
        workers_repo,
        seed_serial_lock,
        engine,
    ):
        async with async_database.transaction() as conn:
            acquired = await workers_repo.take_serial_lock(conn, 'worker-A')

        assert acquired is True
        assert _read_serial_lock_worker(engine) == 'worker-A'

    async def test_cannot_steal_active_lock(
        self,
        async_database,
        workers_repo,
        seed_serial_lock,
        engine,
    ):
        """A second worker MUST NOT overwrite an active owner."""
        async with async_database.transaction() as conn:
            assert await workers_repo.take_serial_lock(conn, 'worker-A') is True

        async with async_database.transaction() as conn:
            stolen = await workers_repo.take_serial_lock(conn, 'worker-B')

        assert stolen is False
        assert _read_serial_lock_worker(engine) == 'worker-A'

    async def test_lock_reusable_after_release(
        self,
        async_database,
        workers_repo,
        seed_serial_lock,
        engine,
    ):
        async with async_database.transaction() as conn:
            assert await workers_repo.take_serial_lock(conn, 'worker-A') is True

        async with async_database.transaction() as conn:
            assert await workers_repo.release_serial_lock(conn, 'worker-A') is True

        assert _read_serial_lock_worker(engine) is None

        async with async_database.transaction() as conn:
            assert await workers_repo.take_serial_lock(conn, 'worker-B') is True

        assert _read_serial_lock_worker(engine) == 'worker-B'


class TestGetNextSerialOperationSkip:
    """``skip`` is a set of operation ids; filter MUST be by id, not name."""

    async def test_empty_skip_returns_first(
        self,
        async_database,
        workers_repo,
        make_serial_operation,
    ):
        first_id = make_serial_operation(name='shared_name')
        make_serial_operation(name='shared_name')

        async with async_database.transaction() as conn:
            op = await workers_repo.get_next_serial_operation(
                conn=conn,
                names={'shared_name'},
                skip=set(),
            )

        assert op is not None
        assert op.id == first_id

    async def test_skip_excludes_by_id(
        self,
        async_database,
        workers_repo,
        make_serial_operation,
    ):
        """Skipping the first id MUST yield the second row of the same name.

        Before the fix the filter compared ``name IN (int_id,)`` which
        coerced to no-match and always returned the first row, defeating
        the loop's "try the next operation" path.
        """
        first_id = make_serial_operation(name='shared_name')
        second_id = make_serial_operation(name='shared_name')

        async with async_database.transaction() as conn:
            op = await workers_repo.get_next_serial_operation(
                conn=conn,
                names={'shared_name'},
                skip={first_id},
            )

        assert op is not None
        assert op.id == second_id

    async def test_skip_all_returns_none(
        self,
        async_database,
        workers_repo,
        make_serial_operation,
    ):
        first_id = make_serial_operation(name='shared_name')
        second_id = make_serial_operation(name='shared_name')

        async with async_database.transaction() as conn:
            op = await workers_repo.get_next_serial_operation(
                conn=conn,
                names={'shared_name'},
                skip={first_id, second_id},
            )

        assert op is None
