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
        self.engine = sa.create_engine(url, pool_pre_ping=True, future=True, echo=echo)

    def connect(self) -> None:
        """Connect to database."""

    def disconnect(self) -> None:
        """Disconnect from the database."""
        try:
            self.engine.dispose()
        except Exception:
            LOG.exception('Exception while disposing database engine')

    def get_large_object(self, oid: int) -> bytes:
        """Return large object."""
        conn = self.engine.raw_connection()
        l_obj = None
        try:
            l_obj = conn.lobject(oid, 'rb')
            content = l_obj.read()
        except Exception:
            LOG.exception('Error loading large object')
            raise
        finally:
            if l_obj is not None:
                l_obj.close()
            conn.close()

        return content

    def delete_large_object(self, oid: int) -> None:
        """Delete large object."""
        conn = self.engine.raw_connection()
        try:
            conn.lobject(oid).unlink()
            conn.commit()
        except Exception:
            LOG.exception('Error deleting large object')
            conn.rollback()
            raise
        finally:
            conn.close()
