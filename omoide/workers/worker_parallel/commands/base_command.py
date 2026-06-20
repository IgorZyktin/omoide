"""Base command class."""

import abc


class Command(abc.ABC):
    """Base command class."""

    @abc.abstractmethod
    async def execute(self) -> tuple[list[str], int]:
        """Start execution of the command."""
