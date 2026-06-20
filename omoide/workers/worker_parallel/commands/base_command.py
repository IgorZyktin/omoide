"""Base command class."""

import abc

from omoide.workers.worker_parallel.models import ParallelCommand


class Command(abc.ABC):
    """Base command class."""

    def __init__(self, dto: ParallelCommand) -> None:
        """Initialize instance."""
        self.dto = dto

    @abc.abstractmethod
    async def execute(self) -> tuple[list[str], int]:
        """Start execution of the command."""
