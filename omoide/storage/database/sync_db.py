"""Common synchronous database connector."""

from collections.abc import Generator
import contextlib

import sqlalchemy as sa
from sqlalchemy.engine import Connection
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import custom_logging

LOG = custom_logging.get_logger(__name__)


class SyncDatabase:
    """Database helper class for Worker."""

    def __init__(self, db_url: str, echo: bool = False) -> None:
        """Initialize instance."""
        self._db_url = db_url
        self._engine = sa.create_engine(
            self._db_url,
            echo=echo,
            pool_pre_ping=True,
        )
        self._session: Session | None = None

    @contextlib.contextmanager
    def life_cycle(self) -> Generator[Engine, None, None]:
        """Ensure that connection is closed at the end."""
        try:
            yield self._engine
        finally:
            self._engine.dispose()

    @contextlib.contextmanager
    def start_session(self) -> Generator[Session, None, None]:
        """Wrapper around SA session."""
        with Session(self._engine) as session:
            self._session = session
            yield session
            self._session = None

    @property
    def session(self) -> Session:
        """Return current session."""
        if self._session is None:
            msg = 'You need to start session before using it'
            raise RuntimeError(msg)
        return self._session

    @contextlib.contextmanager
    def start_transaction(self) -> Generator[Connection, None, None]:
        """Wrapper around SA connection."""
        with self._engine.begin() as conn:
            yield conn
