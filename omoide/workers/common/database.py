"""Common database for workers."""

import sqlalchemy as sa

from omoide import custom_logging

LOG = custom_logging.get_logger(__name__)


class PostgreSQLDatabase:
    """Storage in database."""

    def __init__(self, url: str, *, echo: bool) -> None:
        """Initialize instance."""
        self.url = url
        self.echo = echo
        self.engine = sa.create_engine(url, pool_pre_ping=True, future=True)

    def connect(self) -> None:
        """Connect to database."""

    def disconnect(self) -> None:
        """Disconnect from the database."""
        try:
            self.engine.dispose()
        except Exception:
            LOG.exception('Exception while disposing database engine')
