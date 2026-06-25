"""Tests for ``ParallelPostgreSQLDatabase``.

These target the data-access layer of the parallel worker — every method
that touches ``command_queue_parallel`` plus the OID refcount logic that
the worker depends on for the shared-large-object deletion path.

Adapted from the converter ``test_database.py`` patterns.
"""

import pytest

from omoide import models
from omoide.workers.parallel.database import ParallelPostgreSQLDatabase

from .conftest import _read_log
from .conftest import _read_status


# --- get_parallel_commands ---------------------------------------------


class TestGetParallelCommands:
    """The polling query that drives the worker loop."""

    async def test_returns_empty_list_for_empty_queue(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
    ):
        candidates = await parallel_db.get_parallel_commands(
            batch_size=10, supported_operations=frozenset(['dummy'])
        )
        assert candidates == []

    async def test_returns_created_rows(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        command = make_parallel_command()

        candidates = await parallel_db.get_parallel_commands(
            batch_size=10, supported_operations=frozenset(['dummy'])
        )

        assert [c.id for c in candidates] == [command.id]

    async def test_skips_non_created_statuses(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        """ACTIVE / DONE / FAILED rows MUST NOT be picked up."""
        active = make_parallel_command(status='active')
        done = make_parallel_command(status='done')
        failed = make_parallel_command(status='failed')
        created = make_parallel_command(status='created')

        candidates = await parallel_db.get_parallel_commands(
            batch_size=10, supported_operations=frozenset(['dummy'])
        )

        ids = {c.id for c in candidates}
        assert ids == {created.id}
        assert active.id not in ids
        assert done.id not in ids
        assert failed.id not in ids

    async def test_filters_by_supported_operations(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        wanted = make_parallel_command(name='dummy')
        make_parallel_command(name='hard_delete')

        candidates = await parallel_db.get_parallel_commands(
            batch_size=10, supported_operations=frozenset(['dummy'])
        )

        assert [c.id for c in candidates] == [wanted.id]

    async def test_empty_supported_operations_returns_everything_created(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        """An empty filter MUST NOT be applied — workers default to "any name"."""
        a = make_parallel_command(name='dummy')
        b = make_parallel_command(name='hard_delete')

        candidates = await parallel_db.get_parallel_commands(
            batch_size=10, supported_operations=frozenset()
        )

        assert [c.id for c in candidates] == [a.id, b.id]

    async def test_orders_by_id_and_respects_batch_size(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        first = make_parallel_command()
        second = make_parallel_command()
        make_parallel_command()  # third, must be cut

        candidates = await parallel_db.get_parallel_commands(
            batch_size=2, supported_operations=frozenset(['dummy'])
        )

        assert [c.id for c in candidates] == [first.id, second.id]

    async def test_returns_dataclass_with_expected_fields(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        command = make_parallel_command(
            extras={'item_id': 42, 'oid': 1234}
        )

        (loaded,) = await parallel_db.get_parallel_commands(
            batch_size=1, supported_operations=frozenset(['dummy'])
        )

        assert loaded.id == command.id
        assert loaded.name == 'dummy'
        assert loaded.status == models.CommandStatus.CREATED
        assert loaded.extras == {'item_id': 42, 'oid': 1234}
        assert loaded.log == ''


# --- start_task --------------------------------------------------------


class TestStartTask:
    """The atomic CAS that claims a row exclusively for this worker."""

    async def test_marks_created_row_as_active(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
        engine,
    ):
        command = make_parallel_command()

        ok = await parallel_db.start_task(command)

        assert ok is True
        assert _read_status(engine, command.id) == 'active'

    async def test_returns_false_when_row_is_already_active(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
        engine,
    ):
        """The WHERE-status guard prevents two workers from both winning.

        Without the ``status == CREATED`` filter in the UPDATE, two
        racers would both come back with ``rowcount == 1`` and both
        would proceed to execute the same command.
        """
        command = make_parallel_command(status='active')

        ok = await parallel_db.start_task(command)

        assert ok is False
        assert _read_status(engine, command.id) == 'active'

    async def test_returns_false_when_row_is_done(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
        engine,
    ):
        command = make_parallel_command(status='done')

        ok = await parallel_db.start_task(command)

        assert ok is False
        assert _read_status(engine, command.id) == 'done'

    async def test_returns_false_when_row_is_failed(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
        engine,
    ):
        command = make_parallel_command(status='failed')

        ok = await parallel_db.start_task(command)

        assert ok is False
        assert _read_status(engine, command.id) == 'failed'


# --- mark_done / mark_failed -------------------------------------------


class TestMarkDone:
    async def test_sets_status_to_done(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
        engine,
    ):
        command = make_parallel_command(status='active')

        await parallel_db.mark_done(command)

        assert _read_status(engine, command.id) == 'done'

    async def test_idempotent_on_already_done_row(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
        engine,
    ):
        """``mark_done`` has no status guard — calling it twice is harmless."""
        command = make_parallel_command(status='active')

        await parallel_db.mark_done(command)
        await parallel_db.mark_done(command)

        assert _read_status(engine, command.id) == 'done'


class TestMarkFailed:
    async def test_sets_status_and_log(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
        engine,
    ):
        command = make_parallel_command(status='active')

        await parallel_db.mark_failed(command, error='boom')

        assert _read_status(engine, command.id) == 'failed'
        assert _read_log(engine, command.id) == 'boom'

    async def test_overwrites_previous_log(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
        engine,
    ):
        command = make_parallel_command(status='active')

        await parallel_db.mark_failed(command, error='first')
        await parallel_db.mark_failed(command, error='second')

        assert _read_log(engine, command.id) == 'second'


# --- is_oid_referenced_elsewhere ---------------------------------------


class TestIsOidReferencedElsewhere:
    """The OID-refcount check that gates large-object deletion.

    Mirrors the converter's identical test class, but on the new
    ``command_queue_parallel`` table.
    """

    async def test_true_when_another_row_references_same_oid(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        first = make_parallel_command(extras={'oid': 12345})
        second = make_parallel_command(extras={'oid': 12345})

        assert (
            await parallel_db.is_oid_referenced_elsewhere(
                12345, exclude_id=first.id
            )
            is True
        )
        assert (
            await parallel_db.is_oid_referenced_elsewhere(
                12345, exclude_id=second.id
            )
            is True
        )

    async def test_false_when_only_excluded_row_references_oid(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        only = make_parallel_command(extras={'oid': 12345})

        assert (
            await parallel_db.is_oid_referenced_elsewhere(
                12345, exclude_id=only.id
            )
            is False
        )

    async def test_false_when_oid_is_unknown(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        row = make_parallel_command(extras={'oid': 12345})

        assert (
            await parallel_db.is_oid_referenced_elsewhere(
                99999, exclude_id=row.id
            )
            is False
        )

    async def test_ignores_rows_without_oid(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        target = make_parallel_command(extras={'oid': 12345})
        make_parallel_command(extras={'item_id': 7})
        make_parallel_command(extras={})

        assert (
            await parallel_db.is_oid_referenced_elsewhere(
                12345, exclude_id=target.id
            )
            is False
        )

    async def test_finds_oid_regardless_of_status(
        self,
        parallel_db: ParallelPostgreSQLDatabase,
        make_parallel_command,
    ):
        """A reference is a reference whether the other row is created /
        active / done / failed — the LOB must outlive any of them."""
        owner = make_parallel_command(extras={'oid': 99})
        active = make_parallel_command(extras={'oid': 99}, status='active')

        assert (
            await parallel_db.is_oid_referenced_elsewhere(
                99, exclude_id=owner.id
            )
            is True
        )
        # And of course the symmetric case.
        assert (
            await parallel_db.is_oid_referenced_elsewhere(
                99, exclude_id=active.id
            )
            is True
        )
