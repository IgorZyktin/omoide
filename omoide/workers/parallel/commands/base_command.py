"""Base command class."""

import abc

from omoide import const
from omoide.models import ParallelCommand


class Command(abc.ABC):
    """Base command class."""

    def __init__(self, dto: ParallelCommand) -> None:
        """Initialize instance."""
        self.dto = dto

    @abc.abstractmethod
    async def execute(self) -> int:
        """Start execution of the command."""

    @abc.abstractmethod
    def get_required_resources(self) -> list[const.LockableResource]:
        """Return resources to lock before execution."""
