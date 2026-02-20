"""Application dependencies."""

from omoide.workers.converter.database import PostgreSQLDatabase
from omoide.workers.converter.interfaces import AbsDatabase


def get_database(url: str, *, echo: bool) -> AbsDatabase:
    """Get storage instance."""
    return PostgreSQLDatabase(url=url, echo=echo)
