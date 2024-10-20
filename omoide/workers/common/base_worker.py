"""General worker class for all workers."""

import abc
import signal
from typing import Any
from typing import Generic
from typing import TypeVar

from omoide import custom_logging
from omoide.workers.common.base_cfg import BaseWorkerConfig
from omoide.workers.common.mediator import WorkerMediator

LOG = custom_logging.get_logger(__name__)

ConfigT = TypeVar('ConfigT', bound=BaseWorkerConfig)


class BaseWorker(Generic[ConfigT], abc.ABC):
    """General worker class for all workers."""

    def __init__(self, config: ConfigT, mediator: WorkerMediator) -> None:
        """Initialize instance."""
        self.config = config
        self.mediator = mediator
        self.stopping = False

    def start(self) -> None:
        """Start worker."""
        self.register_signals()
        self.mediator.database.connect()

        with self.mediator.database.transaction() as conn:
            self.mediator.workers.register_worker(conn, self.config.name)

        LOG.info('Worker {!r} started', self.config.name)

    def stop(self) -> None:
        """Start worker."""
        self.mediator.database.disconnect()
        LOG.info('Worker {!r} stopped', self.config.name)

    def register_signals(self) -> None:
        """Decide how we will stop."""

        def signal_handler(signum: int, frame: Any) -> None:
            """Handle signal."""
            _ = frame
            string = signal.strsignal(signum)
            LOG.info('Caught signal {!r}, stopping', string)
            self.stopping = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    @abc.abstractmethod
    def execute(self) -> bool:
        """Perform workload."""
