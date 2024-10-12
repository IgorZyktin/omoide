"""Rebuild known tags for specific user."""

from omoide.workers.serial.operations.base_operation import Operation


class RebuildKnownTags(Operation):
    """Rebuild known tags for specific user."""

    name: str = 'rebuild_known_tags'

    async def execute(self) -> bool:
        """Perform workload."""
        return False
