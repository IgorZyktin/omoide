"""Generic locking mechanism."""

import abc
from collections.abc import Sequence

from omoide import const


class AbsLockingProvider(abc.ABC):
    """Generic locking mechanism."""

    @abc.abstractmethod
    async def connect(self) -> None:
        """Connect to the database."""

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the database."""

    @abc.abstractmethod
    async def acquire(
        self,
        resources: Sequence[const.LockableResource],
    ) -> list[const.LockableResource] | None:
        """Lock all given resources."""

    @abc.abstractmethod
    async def release_held(
        self,
        resources: Sequence[const.LockableResource],
    ) -> None:
        """Release all given resources."""

    @abc.abstractmethod
    async def release_all(self) -> None:
        """Release all resources."""
