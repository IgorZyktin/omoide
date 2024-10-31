"""Repository that performs various operations on different objects."""

import abc
from typing import Generic
from typing import TypeVar

from omoide import models
from omoide.serial_operations import SerialOperation

ConnectionT = TypeVar('ConnectionT')


class AbsMiscRepo(Generic[ConnectionT], abc.ABC):
    """Repository that performs various operations on different objects."""

    @abc.abstractmethod
    async def get_computed_tags(self, conn: ConnectionT, item: models.Item) -> set[str]:
        """Get computed tags for this item."""

    @abc.abstractmethod
    async def create_serial_operation(self, conn: ConnectionT, operation: SerialOperation) -> int:
        """Create serial operation."""
