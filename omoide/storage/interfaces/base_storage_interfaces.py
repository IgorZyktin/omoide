"""Base storage classes."""
import abc
from typing import Any


class AbsStorage(abc.ABC):
    """Base storage class."""

    @abc.abstractmethod
    def transaction(self) -> Any:
        """Start transaction."""
