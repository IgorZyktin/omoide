"""Worker utils."""

import asyncio
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import os
import signal
import sys
import threading
from typing import NoReturn

import python_utilz as pu

from omoide import custom_logging
from omoide.workers.child_init import init_child

LOG = custom_logging.get_logger(__name__)


def signal_handler(
    event: threading.Event,
    deadline: float,
) -> None:
    """Handle shutdown signals."""
    LOG.warning(
        'Received signal. Shutting down gracefully in {deadline} sec.',
        deadline=pu.human_readable_time(deadline),
    )
    event.clear()

    def timeout_handler() -> NoReturn:
        LOG.error('Graceful shutdown timed out, forcing exit')
        sys.exit(1)

    timer = threading.Timer(deadline, timeout_handler)
    timer.daemon = True
    timer.start()


def add_signal_handling(
    event: threading.Event,
    deadline: float,
) -> None:
    """Handle shutdown signals."""
    handler = partial(signal_handler, event=event, deadline=deadline)
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, handler)
    loop.add_signal_handler(signal.SIGTERM, handler)


def get_executor(
    desired_worker_num: int,
    max_worker_num: int,
) -> ProcessPoolExecutor:
    """Get the executor pool. executor instance."""
    cores = desired_worker_num or os.cpu_count() or 1
    cores = min(cores, max_worker_num)
    executor = ProcessPoolExecutor(max_workers=cores, initializer=init_child)
    return executor
