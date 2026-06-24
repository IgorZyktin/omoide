"""Integration tests for ``PGAdvisoryLock``.

Per CLAUDE.md §1 these run against a real PostgreSQL instance. They
deliberately exercise behaviour that only manifests at the driver/server
boundary — connection lifecycle, AUTOCOMMIT, session-scoped lock
ownership — which is exactly what cannot be verified with mocks.
"""

import pytest
import sqlalchemy as sa

from omoide.const import LockableResource
from omoide.infra.implementations.pg_advisory_lock import PGAdvisoryLock

_NS_USER = 1
_NS_ITEM = 2


def _to_async_url(url: str) -> str:
    """Convert a sync-driver Postgres URL to the asyncpg driver."""
    for prefix in ('postgresql+psycopg2://', 'postgresql+psycopg://', 'postgresql://'):
        if url.startswith(prefix):
            return 'postgresql+asyncpg://' + url[len(prefix) :]
    return url


@pytest.fixture
async def lock_engine_url(test_db_url):
    """Provide a dedicated url for AsyncEngine for advisory-lock tests."""
    return _to_async_url(test_db_url)


@pytest.fixture
async def lock_a(lock_engine_url):
    """First advisory-lock provider (acts as worker A)."""
    provider = PGAdvisoryLock(lock_engine_url)
    await provider.connect()
    try:
        yield provider
    finally:
        await provider.disconnect()


@pytest.fixture
async def lock_b(lock_engine_url):
    """Second advisory-lock provider (acts as worker B)."""
    provider = PGAdvisoryLock(lock_engine_url)
    await provider.connect()
    try:
        yield provider
    finally:
        await provider.disconnect()


async def _backend_state_of(
    observer: PGAdvisoryLock,
    target: PGAdvisoryLock,
) -> str | None:
    """Query target's backend state through observer's connection.

    Querying ``pg_stat_activity`` from the same backend whose state we
    want to read returns ``'active'`` (it's actively running that very
    SELECT) and tells us nothing about the steady state — we have to
    look from somewhere else.
    """
    pid_row = await target._connection.execute(sa.text('SELECT pg_backend_pid()'))  # noqa: SLF001
    (target_pid,) = pid_row.fetchone()
    state_row = await observer._connection.execute(  # noqa: SLF001
        sa.text('SELECT state FROM pg_stat_activity WHERE pid = :pid'),
        {'pid': target_pid},
    )
    row = state_row.fetchone()
    return None if row is None else row[0]


async def _count_advisory_locks(provider: PGAdvisoryLock) -> int:
    """Count advisory locks held by this provider's backend."""
    result = await provider._connection.execute(  # noqa: SLF001
        sa.text(
            "SELECT COUNT(*) FROM pg_locks WHERE locktype = 'advisory' AND pid = pg_backend_pid()",
        ),
    )
    (count,) = result.fetchone()
    return int(count)


class TestAcquireAndRelease:
    """Basic lifecycle and cross-session conflict."""

    async def test_acquire_returns_resources_sorted(self, lock_a):
        out_of_order = [
            LockableResource(namespace=_NS_ITEM, affected_id=999),
            LockableResource(namespace=_NS_USER, affected_id=42),
            LockableResource(namespace=_NS_ITEM, affected_id=100),
        ]

        taken = await lock_a.acquire(out_of_order)

        assert taken is not None
        assert taken == sorted(out_of_order)
        await lock_a.release_held(taken)

    async def test_second_provider_cannot_take_held_lock(self, lock_a, lock_b):
        target = [LockableResource(namespace=_NS_USER, affected_id=42)]

        first = await lock_a.acquire(target)
        second = await lock_b.acquire(target)

        assert first is not None
        assert second is None
        await lock_a.release_held(first)

    async def test_second_provider_takes_after_release(self, lock_a, lock_b):
        target = [LockableResource(namespace=_NS_USER, affected_id=42)]

        first = await lock_a.acquire(target)
        assert first is not None
        await lock_a.release_held(first)

        second = await lock_b.acquire(target)
        assert second is not None
        await lock_b.release_held(second)

    async def test_second_provider_takes_after_disconnect(self, lock_engine_url, lock_b):
        """Closing the holding connection releases its session locks."""
        target = [LockableResource(namespace=_NS_USER, affected_id=42)]

        transient = PGAdvisoryLock(lock_engine_url)
        await transient.connect()
        held = await transient.acquire(target)
        assert held is not None

        await transient.disconnect()  # MUST release the lock without unlock calls

        second = await lock_b.acquire(target)
        assert second is not None
        await lock_b.release_held(second)

    async def test_different_resources_do_not_conflict(self, lock_a, lock_b):
        """Different namespaces with the same id MUST NOT conflict."""
        a_target = [LockableResource(namespace=_NS_USER, affected_id=42)]
        b_target = [LockableResource(namespace=_NS_ITEM, affected_id=42)]

        first = await lock_a.acquire(a_target)
        second = await lock_b.acquire(b_target)

        assert first is not None
        assert second is not None

        await lock_a.release_held(first)
        await lock_b.release_held(second)


class TestPartialAcquireRollsBack:
    """If any resource cannot be locked, the already-taken ones MUST be released."""

    async def test_partial_failure_releases_prefix(self, lock_a, lock_b):
        shared = LockableResource(namespace=_NS_ITEM, affected_id=777)
        a_only = LockableResource(namespace=_NS_USER, affected_id=42)

        # B holds the shared resource first.
        b_held = await lock_b.acquire([shared])
        assert b_held is not None

        # A asks for (user, item). Sorted order is (1, 42) then (2, 777).
        # First lock succeeds; second fails; first MUST be released.
        attempted = await lock_a.acquire([a_only, shared])
        assert attempted is None

        # Verify A holds nothing — count its advisory locks server-side.
        assert await _count_advisory_locks(lock_a) == 0

        # And the user resource is now free for B too.
        b_user = await lock_b.acquire([a_only])
        assert b_user is not None

        await lock_b.release_held(b_user)
        await lock_b.release_held(b_held)


class TestAutocommitInvariant:
    """The dedicated connection MUST NOT linger in 'idle in transaction'.

    Without ``isolation_level='AUTOCOMMIT'`` the very first execute() opens
    an implicit transaction that never commits — this test would fail with
    ``state == 'idle in transaction'`` after acquire_all.
    """

    async def test_backend_idle_after_acquire(self, lock_a, lock_b):
        target = [LockableResource(namespace=_NS_USER, affected_id=42)]
        held = await lock_a.acquire(target)
        assert held is not None

        assert await _backend_state_of(observer=lock_b, target=lock_a) == 'idle'

        await lock_a.release_held(held)
        assert await _backend_state_of(observer=lock_b, target=lock_a) == 'idle'


class TestConnectionLifecycle:
    """Calling order and idempotency."""

    async def test_acquire_without_connect_raises(self, lock_engine_url):
        provider = PGAdvisoryLock(lock_engine_url)
        with pytest.raises(RuntimeError, match='Lock connection was not established'):
            await provider.acquire([LockableResource(_NS_USER, 42)])

    async def test_double_connect_is_noop(self, lock_engine_url):
        provider = PGAdvisoryLock(lock_engine_url)
        await provider.connect()
        first_conn = provider._connection  # noqa: SLF001
        await provider.connect()
        assert provider._connection is first_conn  # noqa: SLF001
        await provider.disconnect()

    async def test_double_disconnect_is_noop(self, lock_engine_url):
        provider = PGAdvisoryLock(lock_engine_url)
        await provider.connect()
        await provider.disconnect()
        await provider.disconnect()  # MUST NOT raise
