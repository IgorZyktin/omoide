"""Test."""

import pytest

from omoide import serial_operations as so
from omoide.workers.serial import operations as op


@pytest.mark.asyncio
async def test_serial_operation_dummy(serial_worker):
    # arrange
    worker = serial_worker
    operation = so.SerialOperation.from_name(
        name='dummy',
        extras={},
    )
    executor = op.SerialOperationExecutor.from_operation(
        operation=operation,
        config=worker.config,
        mediator=worker.mediator,
    )

    # act + assert
    await executor.execute()
