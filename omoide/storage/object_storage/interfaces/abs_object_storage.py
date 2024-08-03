"""Abstract base object storage."""
import abc


class AbsObjectStorage(abc.ABC):
    """Abstract base object storage."""

    @abc.abstractmethod
    def save(self) -> int:
        """Save object and return operation id."""

    @abc.abstractmethod
    def delete(self) -> int:
        """Delete object and return operation id."""

    @abc.abstractmethod
    def copy(self) -> int:
        """Copy object and return operation id."""
