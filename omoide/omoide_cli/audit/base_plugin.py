"""Base class for all plugins."""

import abc

from omoide.omoide_cli.audit.database import AuditDatabase


class BasePlugin(abc.ABC):
    """Base class for all plugins."""

    def __init__(self, database: AuditDatabase, *, fix: bool) -> None:
        """Initialize instance."""
        self.database = database
        self.fix = fix

    @abc.abstractmethod
    async def execute(self) -> None:
        """Perform actions."""
