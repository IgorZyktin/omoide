"""Test."""

import pytest

from omoide.workers.serial.worker import SerialWorker


@pytest.mark.asyncio
async def test_serial_operation_rebuild_known_tags_all(
    serial_worker: SerialWorker,
):
    # TODO
    pass