"""Repository that perform worker-related operations."""

import abc
from typing import Generic
from typing import TypeVar

from omoide.models import SerialOperation

ConnectionT = TypeVar('ConnectionT')


class AbsWorkerRepo(Generic[ConnectionT], abc.ABC):
    """Repository that perform worker-related operations."""

    @abc.abstractmethod
    async def register_worker(
        self,
        conn: ConnectionT,
        worker_name: str,
    ) -> None:
        """Ensure we're allowed to run and update starting time."""

    @abc.abstractmethod
    async def take_serial_lock(
        self,
        conn: ConnectionT,
        worker_name: str,
    ) -> bool:
        """Try acquiring the lock, return True on success."""

    @abc.abstractmethod
    async def release_serial_lock(
        self,
        conn: ConnectionT,
        worker_name: str,
    ) -> bool:
        """Try releasing the lock, return True on success."""

    @abc.abstractmethod
    async def get_next_serial_operation(
        self,
        conn: ConnectionT,
    ) -> SerialOperation | None:
        """Return next serial operation."""

    @abc.abstractmethod
    async def lock_serial_operation(
        self,
        conn: ConnectionT,
        operation: SerialOperation,
        worker_name: str,
    ) -> bool:
        """Lock operation, return True on success."""

    @abc.abstractmethod
    async def mark_serial_operation_done(
        self,
        conn: ConnectionT,
        operation: SerialOperation,
    ) -> SerialOperation:
        """Mark operation as done."""

    @abc.abstractmethod
    async def mark_serial_operation_failed(
        self,
        conn: ConnectionT,
        operation: SerialOperation,
        error: str,
    ) -> SerialOperation:
        """Mark operation as failed."""
