"""Interfaces for worker components.
"""
import abc


class AbsStrategy(abc.ABC):
    """How to wait for operations."""

    @abc.abstractmethod
    def start(self) -> None:
        """Prepare to work."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Prepare to exit."""

    @abc.abstractmethod
    def wait(self) -> bool:
        """Block until got command, return True for stop."""

    @abc.abstractmethod
    def adjust(self, done_something: bool) -> None:
        """Adjust behaviour according to result."""


class AbsWorker(abc.ABC):
    """Base worker class."""
    counter: int

    @abc.abstractmethod
    def download_media(self) -> None:
        """Download media from the database."""

    @abc.abstractmethod
    def drop_media(self) -> None:
        """Delete media from the database."""

    @abc.abstractmethod
    def manual_copy(self) -> None:
        """Perform manual copy operations."""

    @abc.abstractmethod
    def drop_manual_copies(self) -> None:
        """Delete copy operations from the DB."""
