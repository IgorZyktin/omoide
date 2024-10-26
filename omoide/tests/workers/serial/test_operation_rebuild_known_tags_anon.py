"""Test."""

import pytest

from omoide import serial_operations as so
from omoide.workers.serial import operations as op
from omoide.workers.serial.worker import SerialWorker


@pytest.mark.asyncio
async def test_serial_operation_rebuild_known_tags_anon(
    serial_worker: SerialWorker,
):
    # arrange
    worker = serial_worker
    operation = so.SerialOperation.from_name(
        name='rebuild_known_tags_anon',
        extras={},
    )
    executor = op.SerialOperationExecutor.from_operation(
        operation=operation,
        config=worker.config,
        mediator=worker.mediator,
    )

    # act + assert
    await executor.execute()


async def arrange(serial_worker: SerialWorker):
    """Arrange test."""
    worker = serial_worker

    async with worker.mediator.database.transaction() as conn:
        await worker.mediator.tags.drop_known_tags_anon(conn)

    # TODO
