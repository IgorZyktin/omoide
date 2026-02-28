"""Repository that performs various operations on different objects."""

import abc
from typing import Any
from typing import Generic
from typing import TypeVar

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsMiscRepo(abc.ABC, Generic[ConnectionT]):
    """Repository that performs various operations on different objects."""

    @abc.abstractmethod
    async def create_serial_operation(
        self,
        conn: ConnectionT,
        name: str,
        extras: dict[str, Any],
        payload: bytes = b'',
    ) -> int:
        """Create serial operation."""

    @abc.abstractmethod
    async def create_parallel_operation(
        self,
        conn: ConnectionT,
        name: str,
        extras: dict[str, Any],
        payload: bytes = b'',
    ) -> int:
        """Create parallel operation."""

    @abc.abstractmethod
    async def save_input_media(
        self,
        conn: ConnectionT,
        media: models.InputMedia,
    ) -> int:
        """Save media from user."""
