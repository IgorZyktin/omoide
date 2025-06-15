"""Base class for all plugins."""

import abc

from omoide.omoide_cli.audit.database import AuditDatabase


class BasePlugin(abc.ABC):
    """Base class for all plugins."""

    def __init__(self, database: AuditDatabase) -> None:
        """Initialize instance."""
        self.database = database

    @abc.abstractmethod
    async def execute(self) -> None:
        """Perform actions."""
