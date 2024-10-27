"""Repository that performs operations with signatures."""

import abc
from typing import Generic
from typing import TypeVar

from omoide import models

ConnectionT = TypeVar('ConnectionT')


class AbsSignaturesRepo(Generic[ConnectionT], abc.ABC):
    """Repository that performs operations with signatures."""

    @abc.abstractmethod
    async def get_md5_signature(
        self,
        conn: ConnectionT,
        item: models.Item,
    ) -> str | None:
        """Get signature record."""

    @abc.abstractmethod
    async def get_md5_signatures(
        self,
        conn: ConnectionT,
        items: list[models.Item],
    ) -> dict[int, str | None]:
        """Get many signatures."""

    @abc.abstractmethod
    async def save_md5_signature(
        self,
        conn: ConnectionT,
        item: models.Item,
        signature: str,
    ) -> None:
        """Create signature record."""

    @abc.abstractmethod
    async def get_cr32_signature(
        self,
        conn: ConnectionT,
        item: models.Item,
    ) -> int | None:
        """Get signature record."""

    @abc.abstractmethod
    async def get_cr32_signatures(
        self,
        conn: ConnectionT,
        items: list[models.Item],
    ) -> dict[int, int | None]:
        """Get many signatures."""

    @abc.abstractmethod
    async def save_cr32_signature(
        self,
        conn: ConnectionT,
        item: models.Item,
        signature: int,
    ) -> None:
        """Create signature record."""
