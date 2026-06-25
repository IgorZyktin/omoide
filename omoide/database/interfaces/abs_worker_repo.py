"""Repository that perform worker-related operations."""

import abc
from collections.abc import Collection
from typing import Generic
from typing import TypeVar

from omoide import operations

ConnectionT = TypeVar('ConnectionT')


class AbsWorkersRepo(abc.ABC, Generic[ConnectionT]):
    """Repository that perform worker-related operations."""

    @abc.abstractmethod
    async def register_worker(self, conn: ConnectionT, worker_name: str) -> None:
        """Ensure we're allowed to run and update starting time."""

    @abc.abstractmethod
    async def take_serial_lock(self, conn: ConnectionT, worker_name: str) -> bool:
        """Try acquiring the lock, return True on success."""

    @abc.abstractmethod
    async def release_serial_lock(self, conn: ConnectionT, worker_name: str) -> bool:
        """Try releasing the lock, return True on success."""

    @abc.abstractmethod
    async def get_next_serial_operation(
        self,
        conn: ConnectionT,
        names: Collection[str],
        skip: set[int],
    ) -> operations.Operation | None:
        """Return next serial operation."""

    @abc.abstractmethod
    async def lock_serial_operation(
        self,
        conn: ConnectionT,
        operation: operations.Operation,
    ) -> bool:
        """Lock operation, return True on success."""

    @abc.abstractmethod
    async def save_serial_operation_as_started(
        self,
        conn: ConnectionT,
        operation: operations.Operation,
    ) -> int:
        """Save operation."""

    @abc.abstractmethod
    async def save_serial_operation_as_completed(
        self,
        conn: ConnectionT,
        operation: operations.Operation,
        processed_by: str,
    ) -> int:
        """Save operation."""

    @abc.abstractmethod
    async def save_serial_operation_as_failed(
        self,
        conn: ConnectionT,
        operation: operations.Operation,
        error: str,
    ) -> int:
        """Save operation."""
