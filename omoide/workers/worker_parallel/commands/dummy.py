"""Dummy command."""

import asyncio

from omoide.workers.worker_parallel.commands.base_command import Command


class DummyCommand(Command):
    """Dummy command."""

    async def execute(self) -> tuple[list[str], int]:
        """Start execution of the command."""
        await asyncio.sleep(10)
        return [], 0
