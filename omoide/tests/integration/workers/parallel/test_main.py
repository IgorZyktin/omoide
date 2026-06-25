"""Tests for the parallel worker loop (``do_work`` / ``_process_one``).

Almost every case uses ``DummyCommand`` because that isolates the
loop / lock / cleanup contract from any specific command's business
logic. ``DummyCommand.get_required_resources()`` is ``[]`` and
``execute()`` is an ``await asyncio.sleep(0)``, so what we exercise here
is exclusively the worker's own behaviour: claim atomically, lock
correctly, mark status correctly, clean up the OID when safe.

Adapted from the converter ``test_main.py`` patterns (empty queue,
happy path, failure, batching, lock-stealing) but rewritten for the
new advisory-lock / TaskGroup architecture.
"""


from omoide import const
from omoide.const import LockableResource
from omoide.infra.implementations.pg_advisory_lock import PGAdvisoryLock
from omoide.workers.parallel import __main__ as parallel_main
from omoide.workers.parallel import commands
from omoide.workers.parallel import metrics

from .conftest import _large_object_exists
from .conftest import _read_log
from .conftest import _read_status
from .conftest import _save_small_large_object


def _kwargs(
    stub_config,
    parallel_db,
    lock_provider,
    metrics_collector,
    users_repo,
    items_repo,
    meta_repo,
    fs_locator,
    object_storage,
):
    """Pack the kwargs for ``do_work``.

    ``executor`` is ``None`` everywhere: ``DummyCommand`` does not call
    ``loop.run_in_executor``, so the parameter is genuinely unused on
    every code path these tests cover. If a future test exercises a
    real CPU command, it should request its own ``ProcessPoolExecutor``
    fixture and override this.
    """
    return {
        'config': stub_config,
        'executor': None,
        'lock': lock_provider,
        'database': parallel_db,
        'metrics_collector': metrics_collector,
        'users_repo': users_repo,
        'items_repo': items_repo,
        'meta_repo': meta_repo,
        'fs_locator': fs_locator,
        'object_storage': object_storage,
    }


# --- empty queue --------------------------------------------------------


class TestEmptyQueue:
    async def test_returns_false_when_no_candidates(
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
    ):
        result = await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )
        assert result is False


# --- happy path: DummyCommand goes from CREATED to DONE -----------------


class TestHappyPathDummy:
    async def test_command_transitions_to_done(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        engine,
    ):
        command = make_parallel_command()

        result = await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert result is True
        assert _read_status(engine, command.id) == 'done'

    async def test_metrics_incremented_on_success(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
    ):
        make_parallel_command()

        await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert metrics_collector.get_value(metrics.COMMANDS_PROCESSED) == 1.0
        assert metrics_collector.get_value(metrics.ERRORS) == 0.0


# --- failure path: execute raises -> mark_failed ------------------------


class TestExecutionFailure:
    async def test_failure_marks_command_failed_with_traceback(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        engine,
        monkeypatch,
    ):
        command = make_parallel_command()

        async def _failing(self):
            msg = 'forced failure'
            raise RuntimeError(msg)

        monkeypatch.setattr(commands.DummyCommand, 'execute', _failing)

        await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert _read_status(engine, command.id) == 'failed'
        assert 'forced failure' in _read_log(engine, command.id)

    async def test_failure_increments_error_metric(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        monkeypatch,
    ):
        make_parallel_command()

        async def _failing(self):
            raise RuntimeError('boom')

        monkeypatch.setattr(commands.DummyCommand, 'execute', _failing)

        await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert metrics_collector.get_value(metrics.ERRORS) == 1.0
        assert metrics_collector.get_value(metrics.COMMANDS_PROCESSED) == 0.0


# --- OID lifecycle ------------------------------------------------------


class TestOidCleanup:
    """The refcount path on ``_cleanup_oid``.

    DummyCommand carries no item / file work, but the worker's OID
    cleanup runs purely off ``extras['oid']``. That makes Dummy + a
    real LOB the cleanest harness for this contract.
    """

    async def test_solo_oid_is_deleted_after_processing(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        engine,
    ):
        oid = await _save_small_large_object(object_storage, b'solo')
        assert _large_object_exists(engine, oid) is True

        command = make_parallel_command(extras={'oid': oid})

        await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert _read_status(engine, command.id) == 'done'
        assert _large_object_exists(engine, oid) is False

    async def test_oid_kept_when_other_row_references_it(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        engine,
    ):
        """An older DONE row in the table still counts as a reference.

        ``is_oid_referenced_elsewhere`` does not filter by status — any
        row with ``extras['oid'] = X`` keeps the LOB alive. The worker
        must respect that and leave the OID intact.
        """
        oid = await _save_small_large_object(object_storage, b'shared')

        # Pretend a prior pass left a done row referencing this OID.
        make_parallel_command(extras={'oid': oid}, status='done')

        fresh = make_parallel_command(extras={'oid': oid})

        await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert _read_status(engine, fresh.id) == 'done'
        assert _large_object_exists(engine, oid) is True


# --- advisory lock gating -----------------------------------------------


class TestAdvisoryLockGate:
    """When a needed resource is already locked, ``process_one`` skips.

    This is the advisory-lock equivalent of the converter's
    ``test_continues_to_next_candidate_when_first_lock_fails``, but for
    the new architecture where contention is signalled by
    ``acquire()`` returning ``None``.
    """

    async def test_command_stays_created_while_oid_lock_is_held(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        async_db_url,
        engine,
    ):
        oid = await _save_small_large_object(object_storage, b'guarded')
        command = make_parallel_command(extras={'oid': oid})

        # A second provider sits on the OID lock — the worker's acquire()
        # will return None and process_one will give up silently.
        squatter = PGAdvisoryLock(async_db_url)
        await squatter.connect()
        try:
            held = await squatter.acquire(
                [LockableResource(const.LockNamespace.LARGE_OBJECTS, oid)]
            )
            assert held is not None

            await parallel_main.do_work(
                **_kwargs(
                    stub_config,
                    parallel_db,
                    lock_provider,
                    metrics_collector,
                    users_repo,
                    items_repo,
                    meta_repo,
                    fs_locator,
                    object_storage,
                )
            )

            assert _read_status(engine, command.id) == 'created'
            assert metrics_collector.get_value(metrics.COMMANDS_PROCESSED) == 0.0
            assert metrics_collector.get_value(metrics.ERRORS) == 0.0
        finally:
            await squatter.disconnect()

        # And once the squatter is gone, the next pass completes normally.
        await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert _read_status(engine, command.id) == 'done'
        assert _large_object_exists(engine, oid) is False


# --- start_task race ----------------------------------------------------


class TestStartTaskRace:
    """If ``start_task`` returns False, ``execute`` MUST NOT be called.

    This is the worker's defence against the race where ``SKIP LOCKED``
    yielded a row that another worker has since claimed and started.
    """

    async def test_execute_is_not_called_when_start_task_loses(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        engine,
        monkeypatch,
    ):
        command = make_parallel_command()

        invocations: list[int] = []
        original_execute = commands.DummyCommand.execute

        async def _tracking_execute(self):
            invocations.append(self.dto.id)
            return await original_execute(self)

        monkeypatch.setattr(commands.DummyCommand, 'execute', _tracking_execute)

        async def _losing_start(_c):
            return False

        monkeypatch.setattr(parallel_db, 'start_task', _losing_start)

        await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert invocations == []
        assert _read_status(engine, command.id) == 'created'
        assert metrics_collector.get_value(metrics.COMMANDS_PROCESSED) == 0.0
        assert metrics_collector.get_value(metrics.ERRORS) == 0.0


# --- TaskGroup concurrency ----------------------------------------------


class TestTaskGroupConcurrency:
    async def test_multiple_dummy_commands_all_done_in_one_pass(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        engine,
    ):
        ids = [make_parallel_command().id for _ in range(5)]

        result = await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert result is True
        for cmd_id in ids:
            assert _read_status(engine, cmd_id) == 'done'
        assert metrics_collector.get_value(metrics.COMMANDS_PROCESSED) == 5.0

    async def test_one_failure_does_not_kill_sibling_tasks(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        engine,
        monkeypatch,
    ):
        """Test that siblings can continue.

        ``process_one`` swallows command-level exceptions so a single
        failing task can never propagate up and cancel its TaskGroup
        siblings.
        """
        first = make_parallel_command()
        target = make_parallel_command()
        third = make_parallel_command()

        original_execute = commands.DummyCommand.execute

        async def _selective_execute(self):
            if self.dto.id == target.id:
                msg = 'only this one'
                raise RuntimeError(msg)
            return await original_execute(self)

        monkeypatch.setattr(commands.DummyCommand, 'execute', _selective_execute)

        await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert _read_status(engine, first.id) == 'done'
        assert _read_status(engine, target.id) == 'failed'
        assert _read_status(engine, third.id) == 'done'
        assert metrics_collector.get_value(metrics.COMMANDS_PROCESSED) == 2.0
        assert metrics_collector.get_value(metrics.ERRORS) == 1.0


# --- supported_operations filter ----------------------------------------


class TestSupportedOperationsFilter:
    async def test_unsupported_command_is_ignored(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        engine,
    ):
        """``stub_config.supported_operations`` defaults to ``{'dummy'}``.

        A command with a name outside the set must not be picked up by
        the polling query — ``do_work`` returns ``False``, status stays
        ``created``.
        """
        unsupported = make_parallel_command(name='hard_delete')

        result = await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert result is False
        assert _read_status(engine, unsupported.id) == 'created'


# --- invalid oid in extras ----------------------------------------------


class TestInvalidOid:
    async def test_invalid_oid_marks_command_failed(  # noqa: PLR0913
        self,
        stub_config,
        parallel_db,
        lock_provider,
        metrics_collector,
        users_repo,
        items_repo,
        meta_repo,
        fs_locator,
        object_storage,
        make_parallel_command,
        engine,
    ):
        """Test raises.

        ``int(oid)`` raises on non-numeric strings; the worker must
        mark the command failed instead of looping forever on it.
        """
        command = make_parallel_command(extras={'oid': 'not-a-number'})

        await parallel_main.do_work(
            **_kwargs(
                stub_config,
                parallel_db,
                lock_provider,
                metrics_collector,
                users_repo,
                items_repo,
                meta_repo,
                fs_locator,
                object_storage,
            )
        )

        assert _read_status(engine, command.id) == 'failed'
        assert 'Invalid oid' in _read_log(engine, command.id)
