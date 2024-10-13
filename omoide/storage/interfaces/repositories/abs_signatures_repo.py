"""Repository that performs operations with signatures."""

import abc

from omoide import models


class AbsSignaturesRepo(abc.ABC):
    """Repository that performs operations with signatures."""

    @abc.abstractmethod
    async def get_md5_signature(self, item: models.Item) -> str | None:
        """Get signature record."""

    @abc.abstractmethod
    async def get_md5_signatures(
        self,
        items: list[models.Item],
    ) -> dict[int, str | None]:
        """Get many signatures."""

    @abc.abstractmethod
    async def save_md5_signature(
        self, item: models.Item, signature: str
    ) -> None:
        """Create signature record."""

    @abc.abstractmethod
    async def get_cr32_signature(self, item: models.Item) -> int | None:
        """Get signature record."""

    @abc.abstractmethod
    async def get_cr32_signatures(
        self,
        items: list[models.Item],
    ) -> dict[int, int | None]:
        """Get many signatures."""

    @abc.abstractmethod
    async def save_cr32_signature(
        self,
        item: models.Item,
        signature: int,
    ) -> None:
        """Create signature record."""
