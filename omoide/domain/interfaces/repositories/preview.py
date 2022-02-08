# -*- coding: utf-8 -*-
"""Repository that performs all preview queries.
"""
import abc
from typing import Optional

from omoide.domain import preview
from omoide.domain.interfaces.repositories.base import AbsRepository


class AbsPreviewRepository(AbsRepository):
    """Repository that performs all preview queries."""

    @abc.abstractmethod
    async def get_extended_item(
            self,
            item_uuid: str,
    ) -> Optional[preview.ExtendedItem]:
        """Return instance of the item."""

    @abc.abstractmethod
    async def get_neighbours(self, item_uuid: str) -> list[str]:
        """Return uuids of all the neighbours."""
