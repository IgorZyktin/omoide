"""Limited list of supported commands."""

from omoide.workers.parallel.commands.dummy import DummyCommand  # noqa: F401
from omoide.workers.parallel.commands.hard_delete import (
    HardDeleteCommand,  # noqa: F401
)
from omoide.workers.parallel.commands.soft_delete import (
    SoftDeleteCommand,  # noqa: F401
)
from omoide.workers.parallel.commands.copy_image import (
    CopyImageCommand,  # noqa: F401
)
