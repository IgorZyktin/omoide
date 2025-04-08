"""Repository that performs various operations on different objects."""

import abc
from typing import Any
from typing import Generic
from typing import TypeVar

ConnectionT = TypeVar('ConnectionT')


class AbsMiscRepo(Generic[ConnectionT], abc.ABC):
    """Repository that performs various operations on different objects."""

    @abc.abstractmethod
    async def create_serial_operation(
        self,
        conn: ConnectionT,
        request: Any,
    ) -> int:
        """Create serial operation."""
