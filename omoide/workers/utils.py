"""Worker utils."""

import signal
import sys
import threading
from typing import Any

import python_utilz as pu

from omoide import custom_logging

LOG = custom_logging.get_logger(__name__)


def signal_handler(
    signum: int,
    frame: Any,
    event: threading.Event,
    deadline: float,
) -> None:
    """Handle shutdown signals."""
    _ = frame

    LOG.warning(
        'Received signal {signame} ({signum}). Shutting down gracefully for {deadline}',
        signame=signal.strsignal(signum),
        signum=signum,
        deadline=pu.human_readable_time(deadline),
    )
    event.clear()

    def timeout_handler():
        LOG.error('Graceful shutdown timed out, forcing exit')
        sys.exit(1)

    timer = threading.Timer(deadline, timeout_handler)
    timer.start()
