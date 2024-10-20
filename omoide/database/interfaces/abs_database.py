"""Abstract databases."""

import abc
from contextlib import contextmanager
from typing import ContextManager
from typing import Generic
from typing import TypeVar

ConnectionT = TypeVar('ConnectionT')


class AbsDatabase(Generic[ConnectionT], abc.ABC):
    """Abstract synchronous database."""

    @abc.abstractmethod
    def connect(self) -> None:
        """Connect to the database."""

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the database."""

    @contextmanager
    @abc.abstractmethod
    def transaction(self) -> ContextManager[ConnectionT]:
        """Start transaction."""
