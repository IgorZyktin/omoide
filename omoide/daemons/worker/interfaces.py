"""Interfaces for worker components.
"""
import abc


class AbsStrategy(abc.ABC):
    """How to wait for operations."""


class AbsWorker(abc.ABC):
    """Base worker class."""

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
