"""Sqlalchemy database."""

from contextlib import contextmanager
from typing import ContextManager
from typing import Generator
from typing import Iterator

from sqlalchemy import Connection
from sqlalchemy import create_engine

from omoide.database.interfaces.abs_database import AbsDatabase


class SqlalchemyDatabase(AbsDatabase[Connection]):
    """Synchronous database."""

    def __init__(self, db_url: str, echo: bool = False) -> None:
        """Initialize instance."""
        self._engine = create_engine(
            db_url,
            echo=echo,
            pool_pre_ping=True,
        )

    def connect(self) -> None:
        """Connect to the database."""

    def disconnect(self) -> None:
        """Disconnect from the database."""
        self._engine.dispose()

    @contextmanager
    def transaction(self) -> Iterator[Connection]:
        """Start transaction."""
        with self._engine.begin() as connection:
            yield connection
