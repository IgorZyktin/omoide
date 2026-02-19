"""Application dependencies."""

from omoide.workers.converter.interfaces import AbsStorage
from omoide.workers.converter.storage import PostgreSQLStorage


def get_storage(url: str, *, echo: bool) -> AbsStorage:
    """Get storage instance."""
    return PostgreSQLStorage(
        url=url,
        echo=echo,
    )
