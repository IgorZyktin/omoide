"""Dummy command."""

import asyncio

from omoide import const
from omoide.workers.parallel.commands.base_command import Command


class DummyCommand(Command):
    """Dummy command."""

    async def execute(self) -> int:
        """Start execution of the command."""
        await asyncio.sleep(0)
        return 0

    def get_required_resources(self) -> list[const.LockableResource]:
        """Return resources to lock before execution."""
        return []
