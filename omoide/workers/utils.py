"""Worker utils."""

import sys
import threading
from typing import NoReturn

import python_utilz as pu

from omoide import custom_logging

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
