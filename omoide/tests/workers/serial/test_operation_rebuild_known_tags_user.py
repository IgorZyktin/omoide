"""Test."""

import pytest

from omoide import serial_operations as so
from omoide.workers.serial import operations as op
from omoide.workers.serial.worker import SerialWorker


@pytest.mark.asyncio
async def test_serial_operation_rebuild_known_tags_user(
    serial_worker: SerialWorker,
):
    # TODO
    pass
