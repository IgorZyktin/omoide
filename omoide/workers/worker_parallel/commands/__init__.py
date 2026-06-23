"""Limited list of supported commands."""

from omoide.workers.worker_parallel.commands.dummy import DummyCommand  # noqa: F401
from omoide.workers.worker_parallel.commands.hard_delete import (
    HardDeleteCommand,  # noqa: F401
)
from omoide.workers.worker_parallel.commands.soft_delete import (
    SoftDeleteCommand,  # noqa: F401
)
